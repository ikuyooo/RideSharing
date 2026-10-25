"""Evaluate Revision 9 geographic edge cases (Sections 2.3, 25.2, 72.2) on REAL
data against one service_areas version, using the production classification
code and the OSRM car profile. Nothing is persisted.

On CANDIDATE geometry the outcomes are review evidence; acceptance status stays
NOT_VERIFIED until the owner approves a geometry (P1-D1 / P1-D3).

Points are OSM objects named in the rules file / Revision 9 examples (resolved
from the places export). Boundary pairs (15 km, 150 km) are chosen by a
deterministic rule from OSM place nodes - never hardcoded coordinates.

Run (compose): docker compose --profile service-area run --rm service-area-build \
    python -m app.modules.trip.boundary_eval --version <service_area_version>
"""

import argparse
import json
import math
from pathlib import Path
from typing import Any

import httpx
from sqlalchemy import create_engine, text
from sqlalchemy.orm import Session

from app.core.config_baseline import get_config_baseline
from app.core.settings import get_settings
from app.modules.routing.service import OsrmCarDistance, RouteNotFound, RoutingUnavailable
from app.modules.trip import rules
from app.modules.trip.service import point_membership

Lonlat = tuple[float, float]
CANDIDATE_PLACES = {"village", "hamlet", "neighbourhood", "quarter", "suburb", "town", "city", "isolated_dwelling"}
# OSM objects used by Revision 9 examples (resolved in the P1 rules files).
PHENIKAA = "way/973433275"      # Đại học Phenikaa (Sections 16.1, 72.2)
LA_PHU = "node/12147486706"     # La Phù (Section 72.2)
PHO_HIEN = "node/13155709564"   # Phố Hiến - TP Hưng Yên representative (A8)
HA_DONG = "node/13709983624"    # Hà Đông (Section 25.2 example origin)
ANCHOR = "node/74132064"        # Hà Nội admin_centre (A4)


def load_places(path: Path) -> dict[str, dict[str, Any]]:
    out = {}
    with path.open(encoding="utf-8") as fh:
        for line in fh:
            line = line.strip().lstrip("\x1e")
            if not line:
                continue
            f = json.loads(line)
            if f["geometry"]["type"] == "LineString":
                continue
            p = f["properties"]
            out[f"{p['@type']}/{p['@id']}"] = {"name": p.get("name"), "place": p.get("place"), "geometry": f["geometry"]}
    return out


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


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--version", required=True)
    parser.add_argument("--places", type=Path, default=Path("/osm/service_area/places.geojsonseq"))
    parser.add_argument("--out", type=Path, default=Path("/out"))
    # Use a different name when re-evaluating an older bundle so its original
    # evidence files are never overwritten.
    parser.add_argument("--report-name", default="TRIP_CLASSIFICATION_EVAL")
    args = parser.parse_args()

    settings = get_settings()
    baseline = get_config_baseline()
    buffer_km = float(baseline["spatial_and_service_areas"]["urban_boundary_buffer_km"])
    max_km = float(baseline["spatial_and_service_areas"]["max_total_service_radius_km"])
    places = load_places(args.places)
    client = OsrmCarDistance(settings.osrm_car_url, settings.routing_timeout_s)
    engine = create_engine(settings.database_url)
    cases: list[dict[str, Any]] = []

    with Session(engine) as session:
        status = dict(session.execute(text("SELECT area_type, status FROM service_areas WHERE service_area_version = :v"),
                                      {"v": args.version}).tuples().all())
        if set(status) != {"URBAN", "TOTAL"}:
            raise SystemExit(f"version {args.version} not found")
        geometry_status = "/".join(sorted(set(status.values())))

        def point(ref: str) -> Lonlat:
            row = session.execute(text("SELECT ST_X(p), ST_Y(p) FROM (SELECT ST_PointOnSurface(ST_MakeValid("
                                       "ST_SetSRID(ST_GeomFromGeoJSON(:g), 4326))) AS p) s"),
                                  {"g": json.dumps(places[ref]["geometry"])}).one()
            return (row[0], row[1])

        def member(p: Lonlat) -> dict[str, bool]:
            return point_membership(session, args.version, p)

        def classify(case: str, section: str, expected: str, a_ref: str, b_ref: str, a: Lonlat, b: Lonlat,
                     note: str = "", **extra: Any) -> None:
            pa, pb = member(a), member(b)
            row: dict[str, Any] = {"case": case, "section": section, "expected": expected, "pickup": a_ref,
                                   "pickup_name": places[a_ref]["name"] if a_ref in places else "",
                                   "dropoff": b_ref, "dropoff_name": places[b_ref]["name"] if b_ref in places else "",
                                   "pickup_urban": pa["URBAN"], "dropoff_urban": pb["URBAN"],
                                   "pickup_total": pa["TOTAL"], "dropoff_total": pb["TOTAL"], "note": note} | extra
            try:
                c = rules.classify(pa["TOTAL"], pb["TOTAL"], pa["URBAN"], pb["URBAN"],
                                   lambda: client.road_distance(a, b).km, buffer_km)
                row |= {"actual": c.mode or c.error_code, "branch": c.step, "direct_distance_km": c.direct_distance_km}
            except (RouteNotFound, RoutingUnavailable) as exc:
                row |= {"actual": type(exc).__name__, "branch": "routing", "direct_distance_km": None}
            cases.append(row)

        phenikaa, anchor = point(PHENIKAA), point(ANCHOR)

        # 72.2 #1: Phenikaa -> La Phù must be URBAN, La Phù being just outside the urban polygon.
        classify("Phenikaa → La Phù", "72.2", "URBAN", PHENIKAA, LA_PHU, phenikaa, point(LA_PHU),
                 note="spec implies La Phù outside urban polygon -> branch 2b (buffer)", expected_branch="2b")

        # 72.2 #2: ~3 km trip with both ends inside former TP Hưng Yên (A8 representative).
        hy = point(PHO_HIEN)
        near = [(ref, p) for ref, p in places.items()
                if ref.startswith("node/") and p["place"] in CANDIDATE_PLACES and ref != PHO_HIEN
                and 1.5 <= haversine_km(hy, tuple(p["geometry"]["coordinates"])) <= 4.0]
        dists = road_km_from(settings.osrm_car_url, hy, [tuple(p["geometry"]["coordinates"]) for _, p in near])
        pick = min(((abs(d - 3.0), ref, d) for (ref, _), d in zip(near, dists, strict=True) if d is not None), default=None)
        if pick:
            classify("~3 km inside TP Hưng Yên", "72.2", "UNSUPPORTED_INTER_PROVINCE_ROUTE", PHO_HIEN, pick[1], hy,
                     tuple(places[pick[1]]["geometry"]["coordinates"]), note="dropoff = place node closest to 3.0 km road",
                     selected_road_km=round(pick[2], 3))

        # 2.3 buffer: largest road distance <= 15 km and smallest > 15 km from Phenikaa to non-urban places.
        cand = [(ref, tuple(p["geometry"]["coordinates"])) for ref, p in places.items()
                if ref.startswith("node/") and p["place"] in CANDIDATE_PLACES
                and 8 <= haversine_km(phenikaa, tuple(p["geometry"]["coordinates"])) <= 25]
        cand = [(ref, xy) for ref, xy in cand if not member(xy)["URBAN"] and member(xy)["TOTAL"]]
        dists = road_km_from(settings.osrm_car_url, phenikaa, [xy for _, xy in cand])
        pairs = [(d, ref, xy) for (ref, xy), d in zip(cand, dists, strict=True) if d is not None]
        for label, sel, expected in (("<= 15 km", max((p for p in pairs if p[0] <= buffer_km), default=None), "URBAN"),
                                     ("> 15 km", min((p for p in pairs if p[0] > buffer_km), default=None), "INTERCITY")):
            if sel:
                classify(f"buffer {label} from Phenikaa", "2.3", expected, PHENIKAA, sel[1], phenikaa, sel[2],
                         selected_road_km=round(sel[0], 3))

        # 150 km: places inside the routing bbox closest to the limit on each side (from the anchor).
        bbox = tuple(float(x) for x in session.execute(text(
            "SELECT source_json->'manifest'->>'bbox' FROM service_areas WHERE service_area_version=:v LIMIT 1"),
            {"v": args.version}).scalar_one().split(","))
        cand = [(ref, tuple(p["geometry"]["coordinates"])) for ref, p in places.items()
                if ref.startswith("node/") and p["place"] in CANDIDATE_PLACES
                and bbox[0] <= p["geometry"]["coordinates"][0] <= bbox[2] and bbox[1] <= p["geometry"]["coordinates"][1] <= bbox[3]
                and 100 <= haversine_km(anchor, tuple(p["geometry"]["coordinates"])) <= 160]
        dists = road_km_from(settings.osrm_car_url, anchor, [xy for _, xy in cand])
        pairs = [(d, ref, xy) for (ref, xy), d in zip(cand, dists, strict=True) if d is not None]
        for label, sel, expected in (("<= 150 km", max((p for p in pairs if p[0] <= max_km), default=None), "INTERCITY"),
                                     ("> 150 km", min((p for p in pairs if p[0] > max_km), default=None), "OUT_OF_SERVICE_AREA")):
            if sel:
                classify(f"limit {label} from anchor", "2.3 / Baseline max_total_service_radius_km", expected, ANCHOR,
                         sel[1], anchor, sel[2], selected_road_km=round(sel[0], 3),
                         note="membership is decided by the unit polygon (unit chosen by its representative point)")

        # A8 context: Hà Đông -> Phố Hiến vs the 65 km example of Section 25.2.
        try:
            km = client.road_distance(point(HA_DONG), hy).km
            context = {"case": "A8 context: Hà Đông → Phố Hiến road distance", "section": "25.2",
                       "revision9_value_km": 65.0, "osrm_km": round(km, 3),
                       "relative_difference": round((km - 65.0) / 65.0, 4)}
        except (RouteNotFound, RoutingUnavailable) as exc:
            context = {"case": "A8 context", "error": type(exc).__name__}

    for c in cases:
        ok = c["actual"] == c["expected"]
        if ok and c.get("expected_branch") and c["branch"] != c["expected_branch"]:
            c["result_on_candidate"] = f"PASS (mode) / branch {c['branch']} ≠ expected {c['expected_branch']}"
        else:
            c["result_on_candidate"] = "PASS" if ok else "FAIL"
        c["acceptance_status"] = "NOT_VERIFIED (geometry not approved)" if "APPROVED" not in status.values() else (
            "PASS" if ok else "FAIL")
        c["service_area_version"] = args.version
    out_dir = args.out / args.version
    out_dir.mkdir(parents=True, exist_ok=True)
    json_path = out_dir / f"{args.report_name.lower()}.json"
    md_path = out_dir / f"{args.report_name}.md"
    for path in (json_path, md_path):
        if path.exists() and args.report_name == "TRIP_CLASSIFICATION_EVAL" and (out_dir / "REVIEW.md").exists() \
                and "sa_rules_candidate_v1" in (out_dir / "REVIEW.md").read_text(encoding="utf-8"):
            raise SystemExit(f"refusing to overwrite original evidence {path}; pass --report-name")
    json_path.write_text(
        json.dumps({"cases": cases, "context_checks": [context]}, ensure_ascii=False, indent=2), encoding="utf-8")
    lines = [
        f"# Geographic edge cases on real data — `{args.version}` ({geometry_status})",
        "",
        f"Production classification (`app.modules.trip.rules.classify`) + OSRM car road distance (P1-D2). "
        f"Buffer {buffer_km} km and limit {max_km} km from the baseline. Coordinates: OSM objects from the places export "
        "(`@type/@id` below; ways/relations use `ST_PointOnSurface`).",
        "",
        "| Case | R9 § | Pickup (OSM) | Dropoff (OSM) | Road km | Expected | Actual | Branch | Result on candidate | Acceptance |",
        "|---|---|---|---|---|---|---|---|---|---|",
        *[f"| {c['case']} | {c['section']} | {c['pickup']} {c['pickup_name'] or ''} | {c['dropoff']} {c['dropoff_name'] or ''} | "
          f"{c['direct_distance_km'] if c['direct_distance_km'] is not None else c.get('selected_road_km', '—')} | {c['expected']} | "
          f"{c['actual']} | {c['branch']} | **{c['result_on_candidate']}** | {c['acceptance_status']} |" for c in cases],
        "",
        "Context check (A8):",
        "",
        "```json",
        json.dumps(context, ensure_ascii=False, indent=2),
        "```",
        "",
    ]
    md_path.write_text("\n".join(lines), encoding="utf-8")
    print("\n".join(lines))


if __name__ == "__main__":
    main()
