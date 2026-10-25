"""Evaluate Section 2.3 / 72.2 boundary cases on REAL data against one
service_areas version, using the production classification code and the OSRM
car profile. Nothing is persisted.

When the version is CANDIDATE the results are review evidence for the owner,
not acceptance (owner decisions P1-D1 / P1-D3).

Test points come from the OSM places export; the 15 km pair is selected by a
deterministic rule (largest road distance <= buffer and smallest > buffer from
the Phenikaa point), never hardcoded.

Run (compose): docker compose --profile service-area run --rm service-area-build \
    python -m app.modules.trip.boundary_eval --version <service_area_version>
"""

import argparse
import json
import math
from pathlib import Path
from typing import Any

import httpx
import yaml
from sqlalchemy import create_engine, text
from sqlalchemy.orm import Session

from app.core.config_baseline import get_config_baseline
from app.core.settings import get_settings
from app.modules.routing.service import OsrmCarDistance, RouteNotFound, RoutingUnavailable
from app.modules.trip import rules
from app.modules.trip.service import point_membership

Lonlat = tuple[float, float]
CANDIDATE_PLACES = {"village", "hamlet", "neighbourhood", "quarter", "suburb", "town", "city", "isolated_dwelling"}


def load_places(path: Path) -> dict[str, dict[str, Any]]:
    """'node/123' / 'way/456' -> {name, place, lonlat}. Ways use their first vertex
    only for lookup by id; point-on-surface comes from the OSM export geometry."""
    out = {}
    with path.open(encoding="utf-8") as fh:
        for line in fh:
            line = line.strip().lstrip("\x1e")
            if not line:
                continue
            f = json.loads(line)
            p = f["properties"]
            out[f"{p['@type']}/{p['@id']}"] = {"name": p.get("name"), "place": p.get("place"), "geometry": f["geometry"]}
    return out


def representative_point(session: Session, geometry: dict[str, Any]) -> Lonlat:
    row = session.execute(text("SELECT ST_X(p), ST_Y(p) FROM (SELECT ST_PointOnSurface(ST_MakeValid("
                               "ST_SetSRID(ST_GeomFromGeoJSON(:g), 4326))) AS p) s"),
                          {"g": json.dumps(geometry)}).one()
    return (row[0], row[1])


def haversine_km(a: Lonlat, b: Lonlat) -> float:
    lon1, lat1, lon2, lat2 = map(math.radians, (*a, *b))
    h = math.sin((lat2 - lat1) / 2) ** 2 + math.cos(lat1) * math.cos(lat2) * math.sin((lon2 - lon1) / 2) ** 2
    return 2 * 6371.0088 * math.asin(math.sqrt(h))


def road_km_from(osrm_url: str, origin: Lonlat, points: list[Lonlat]) -> list[float | None]:
    out: list[float | None] = []
    for i in range(0, len(points), 150):
        batch = points[i:i + 150]
        coords = ";".join(f"{x:.6f},{y:.6f}" for x, y in [origin, *batch])
        body = httpx.get(f"{osrm_url}/table/v1/driving/{coords}", params={"sources": "0", "annotations": "distance"},
                         headers={"Connection": "close"}, timeout=60).json()
        out.extend(None if d is None else d / 1000 for d in body["distances"][0][1:])
    return out


def classify_pair(session: Session, version: str, client: OsrmCarDistance, buffer_km: float,
                  a: Lonlat, b: Lonlat) -> dict[str, Any]:
    pa, pb = point_membership(session, version, a), point_membership(session, version, b)
    try:
        c = rules.classify(pa["TOTAL"], pb["TOTAL"], pa["URBAN"], pb["URBAN"],
                           lambda: client.road_distance(a, b).km, buffer_km)
        return {"mode": c.mode, "error_code": c.error_code, "step": c.step, "direct_distance_km": c.direct_distance_km,
                "pickup_urban": pa["URBAN"], "dropoff_urban": pb["URBAN"]}
    except (RouteNotFound, RoutingUnavailable) as exc:
        return {"mode": None, "error_code": type(exc).__name__, "step": "routing"}


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--version", required=True)
    parser.add_argument("--places", type=Path, default=Path("/osm/service_area/places.geojsonseq"))
    parser.add_argument("--rules", type=Path, default=Path("/app/config/service_area_rules.candidate.yaml"))
    parser.add_argument("--out", type=Path, default=Path("/out"))
    args = parser.parse_args()

    settings = get_settings()
    buffer_km = float(get_config_baseline()["spatial_and_service_areas"]["urban_boundary_buffer_km"])
    rules_cfg = yaml.safe_load(args.rules.read_text(encoding="utf-8"))
    loc = {t["label"]: t["osm"] for t in rules_cfg["test_locations"]}
    places = load_places(args.places)
    client = OsrmCarDistance(settings.osrm_car_url, settings.routing_timeout_s)
    engine = create_engine(settings.database_url)
    cases: list[dict[str, Any]] = []

    with Session(engine) as session:
        status = dict(session.execute(text("SELECT area_type, status FROM service_areas WHERE service_area_version = :v"),
                                      {"v": args.version}).tuples().all())
        if set(status) != {"URBAN", "TOTAL"}:
            raise SystemExit(f"version {args.version} not found")

        def point(ref: str) -> Lonlat:
            return representative_point(session, places[ref]["geometry"])

        phenikaa = point(loc["Đại học Phenikaa"])
        # Case A - Section 72.2: Phenikaa -> La Phù must be URBAN.
        cases.append({"case": "72.2 Phenikaa -> La Phù", "expected": "URBAN",
                      "pickup": loc["Đại học Phenikaa"], "dropoff": loc["La Phù"]}
                     | classify_pair(session, args.version, client, buffer_km, phenikaa, point(loc["La Phù"])))

        # Case B - Section 72.2: ~3 km trip with both ends inside former TP Hưng Yên.
        hy_ref = loc["Phố Hiến (former TP Hưng Yên)"]
        hy = point(hy_ref)
        near = [(ref, p) for ref, p in places.items()
                if ref.startswith("node/") and p["place"] in CANDIDATE_PLACES and ref != hy_ref
                and 1.5 <= haversine_km(hy, tuple(p["geometry"]["coordinates"])) <= 4.0]
        dists = road_km_from(settings.osrm_car_url, hy, [tuple(p["geometry"]["coordinates"]) for _, p in near])
        scored = sorted(((abs(d - 3.0), ref, d) for (ref, _), d in zip(near, dists, strict=True) if d is not None))
        if scored:
            _, ref, d = scored[0]
            cases.append({"case": "72.2 ~3 km inside former TP Hưng Yên", "expected": "UNSUPPORTED_INTER_PROVINCE_ROUTE",
                          "pickup": hy_ref, "dropoff": ref, "dropoff_name": places[ref]["name"], "road_km_selected": round(d, 3)}
                         | classify_pair(session, args.version, client, buffer_km, hy, tuple(places[ref]["geometry"]["coordinates"])))

        # Case C - 15 km buffer boundary from Phenikaa to places outside the urban area.
        outside = [(ref, p) for ref, p in places.items()
                   if ref.startswith("node/") and p["place"] in CANDIDATE_PLACES
                   and 8 <= haversine_km(phenikaa, tuple(p["geometry"]["coordinates"])) <= 25]
        outside = [(ref, p) for ref, p in outside
                   if not point_membership(session, args.version, tuple(p["geometry"]["coordinates"]))["URBAN"]
                   and point_membership(session, args.version, tuple(p["geometry"]["coordinates"]))["TOTAL"]]
        dists = road_km_from(settings.osrm_car_url, phenikaa, [tuple(p["geometry"]["coordinates"]) for _, p in outside])
        pairs = [(d, ref) for (ref, _), d in zip(outside, dists, strict=True) if d is not None]
        at_or_below = max((x for x in pairs if x[0] <= buffer_km), default=None)
        above = min((x for x in pairs if x[0] > buffer_km), default=None)
        for label, pick, expected in (("<= 15 km", at_or_below, "URBAN"), ("> 15 km", above, "INTERCITY")):
            if pick is None:
                cases.append({"case": f"buffer {label}", "expected": expected, "mode": None, "error_code": "NO_CANDIDATE"})
                continue
            d, ref = pick
            cases.append({"case": f"buffer {label} from Phenikaa", "expected": expected, "pickup": loc["Đại học Phenikaa"],
                          "dropoff": ref, "dropoff_name": places[ref]["name"], "road_km_selected": round(d, 3)}
                         | classify_pair(session, args.version, client, buffer_km, phenikaa,
                                         tuple(places[ref]["geometry"]["coordinates"])))

        # Case D - destination outside the total area: the place=city/town node
        # outside TOTAL that is nearest to the anchor (deterministic choice).
        anchor_ref = f"node/{rules_cfg['total']['anchor']['osm_node']}"
        anchor = tuple(places[anchor_ref]["geometry"]["coordinates"])
        towns = sorted((haversine_km(anchor, tuple(p["geometry"]["coordinates"])), ref)
                       for ref, p in places.items() if ref.startswith("node/") and p["place"] in ("city", "town"))
        outside_ref = next((ref for _, ref in towns
                            if not point_membership(session, args.version, tuple(places[ref]["geometry"]["coordinates"]))["TOTAL"]),
                           None)
        if outside_ref is None:
            cases.append({"case": "outside coverage", "expected": "OUT_OF_SERVICE_AREA", "mode": None,
                          "error_code": "NO_CANDIDATE"})
        else:
            cases.append({"case": "outside coverage: anchor -> nearest town/city outside TOTAL",
                          "expected": "OUT_OF_SERVICE_AREA", "pickup": anchor_ref, "dropoff": outside_ref,
                          "dropoff_name": places[outside_ref]["name"]}
                         | classify_pair(session, args.version, client, buffer_km, anchor,
                                         tuple(places[outside_ref]["geometry"]["coordinates"])))

    for c in cases:
        actual = c.get("mode") or c.get("error_code")
        c["result"] = "AS_EXPECTED" if actual == c["expected"] else "MISMATCH"
        # Section 72.2 expects La Phù outside the urban polygon, i.e. URBAN via the
        # 15 km buffer (step 2b). Reaching URBAN through step 2a is a different path.
        if c["case"].startswith("72.2 Phenikaa") and c.get("step") == "2a":
            c["result"] = "AS_EXPECTED_MODE_BUT_DIFFERENT_PATH (2a, spec implies 2b)"
    geometry_status = "/".join(sorted(set(status.values())))
    out_dir = args.out / args.version
    out_dir.mkdir(parents=True, exist_ok=True)
    (out_dir / "trip_classification_eval.json").write_text(json.dumps(cases, ensure_ascii=False, indent=2), encoding="utf-8")
    lines = [
        f"# Trip classification on real data — `{args.version}` ({geometry_status})",
        "",
        "Production classification code + OSRM car road distance (P1-D2). "
        + ("**Geometry is CANDIDATE: review evidence only, not acceptance.**" if "APPROVED" not in status.values() else ""),
        f"Buffer (baseline urban_boundary_buffer_km): {buffer_km} km.",
        "",
        "| Case | Pickup | Dropoff | Road km | Step | Result mode/error | Expected | Outcome |",
        "|---|---|---|---|---|---|---|---|",
        *[f"| {c['case']} | {c.get('pickup', '—')} | {c.get('dropoff', '—')} {c.get('dropoff_name') or ''} | "
          f"{c.get('direct_distance_km') if c.get('direct_distance_km') is not None else c.get('road_km_selected', '—')} | "
          f"{c.get('step', '—')} | {c.get('mode') or c.get('error_code')} | {c['expected']} | **{c['result']}** |" for c in cases],
        "",
    ]
    (out_dir / "TRIP_CLASSIFICATION_EVAL.md").write_text("\n".join(lines), encoding="utf-8")
    print("\n".join(lines))


if __name__ == "__main__":
    main()
