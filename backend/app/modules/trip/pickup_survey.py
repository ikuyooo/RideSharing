"""GEO-D: tier-2 rejection rate on realistic pickup coordinates.

Points: OSM nodes exported by scripts/osm/export_pickup_candidates.sh (bus stops,
schools, hospitals, markets, ... and settlement place nodes) that lie in the
accept-able polygon (TOTAL minus EXCLUDED) of one version. Deterministic sample
(seed 1): up to PER_PROVINCE points per province, each category in proportion.
Each point gets the production tier-2 rule (rules.point_reason) from one OSRM car
/table request per batch, with the version's exclusions. Report only.

Run (compose): docker compose --profile service-area run --rm service-area-build \
    python -m app.modules.trip.pickup_survey --version <service_area_version>
"""

import argparse
import json
import random
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any

import httpx
from sqlalchemy import create_engine, text

from app.core.settings import get_settings
from app.modules.trip import rules

PER_PROVINCE = 300
SEED = 1
BATCH = 150


def category(p: dict[str, Any]) -> str:
    if p.get("highway") == "bus_stop":
        return "bus_stop"
    if p.get("amenity"):
        return f"amenity={p['amenity']}"
    return f"place={p.get('place')}"


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--version", required=True)
    parser.add_argument("--sources", type=Path, default=Path("/osm/service_area"))
    parser.add_argument("--out", type=Path, default=Path("/out"))
    args = parser.parse_args()
    settings = get_settings()

    pts = []
    with (args.sources / "pickup_candidates.geojsonseq").open(encoding="utf-8") as fh:
        for raw in fh:
            raw = raw.strip().lstrip("\x1e")
            if raw:
                f = json.loads(raw)
                x, y = f["geometry"]["coordinates"]
                pts.append({"id": f["properties"]["@id"], "cat": category(f["properties"]), "x": x, "y": y})
    engine = create_engine(settings.database_url)
    with engine.begin() as conn:
        raw_s = conn.execute(text("SELECT source_json->'serviceability' FROM service_areas "
                                  "WHERE service_area_version = :v AND area_type = 'TOTAL'"), {"v": args.version}).scalar_one()
        if raw_s is None:
            raise SystemExit(f"{args.version} has no serviceability layer")
        conn.execute(text("CREATE TEMP TABLE cand (id bigint, cat text, x float8, y float8)"))
        conn.execute(text("INSERT INTO cand VALUES (:id, :cat, :x, :y)"), pts)
        # Point-in-polygon against ST_Subdivide pieces with a GIST index (the raw TOTAL is
        # one large multipolygon; testing 50k points against it directly is very slow).
        conn.execute(text("CREATE INDEX ON cand USING gist (ST_SetSRID(ST_MakePoint(x, y), 4326))"))
        for layer in ("TOTAL", "EXCLUDED"):
            conn.execute(text(f"""CREATE TEMP TABLE piece_{layer.lower()} AS SELECT ST_Subdivide(geom, 255) AS g
                FROM service_areas WHERE service_area_version = :v AND area_type = :a"""), {"v": args.version, "a": layer})
            conn.execute(text(f"CREATE INDEX ON piece_{layer.lower()} USING gist (g)"))
        rows = conn.execute(text("""SELECT c.id, c.cat, c.x, c.y FROM cand c
            WHERE EXISTS (SELECT 1 FROM piece_total t WHERE ST_Intersects(t.g, ST_SetSRID(ST_MakePoint(c.x, c.y), 4326)))
              AND NOT EXISTS (SELECT 1 FROM piece_excluded e
                              WHERE ST_Intersects(e.g, ST_SetSRID(ST_MakePoint(c.x, c.y), 4326)))
            ORDER BY c.id""")).mappings().all()
    by_province = assign_provinces(args.sources, rows)
    rng = random.Random(SEED)
    sample: list[dict[str, Any]] = []
    for prov, items in sorted(by_province.items()):
        items = sorted(items, key=lambda r: r["id"])
        sample.extend(rng.sample(items, min(PER_PROVINCE, len(items))))

    s = raw_s
    anchor = (float(s["anchor"]["lon"]), float(s["anchor"]["lat"]))
    exclude = ",".join(s.get("exclude", []))
    params = {"sources": "0", "annotations": "distance"} | ({"exclude": exclude} if exclude else {})
    for i in range(0, len(sample), BATCH):
        batch = sample[i:i + BATCH]
        coords = ";".join(f"{x:.6f},{y:.6f}" for x, y in [anchor, *[(r["x"], r["y"]) for r in batch]])
        body = httpx.get(f"{settings.osrm_car_url}/table/v1/driving/{coords}", params=params,
                         headers={"Connection": "close"}, timeout=120).json()
        for j, r in enumerate(batch):
            d = body["distances"][0][j + 1]
            r["road_km"] = None if d is None else d / 1000
            r["snap_m"] = body["destinations"][j + 1]["distance"]
            r["outcome"] = rules.point_reason(r["snap_m"], r["road_km"], float(s["max_snap_m"]),
                                              float(s["max_road_km"])) or "SERVED"

    def table(key: str) -> dict[str, dict[str, int]]:
        out: dict[str, Counter] = defaultdict(Counter)
        for r in sample:
            out[r[key]][r["outcome"]] += 1
        return {k: dict(v) for k, v in sorted(out.items())}

    snaps = sorted(r["snap_m"] for r in sample)
    report = {"service_area_version": args.version, "max_snap_m": s["max_snap_m"], "exclude": s.get("exclude", []),
              "candidates_in_area": len(rows), "sampled": len(sample), "per_province_cap": PER_PROVINCE, "seed": SEED,
              "overall": dict(Counter(r["outcome"] for r in sample)),
              "snap_m_percentiles": {q: round(snaps[min(len(snaps) - 1, int(q / 100 * len(snaps)))], 1)
                                     for q in (50, 90, 95, 99)} if snaps else {},
              "by_province": table("province"), "by_category": table("cat")}
    path = args.out / args.version / "PICKUP_SURVEY.json"
    if path.exists():
        raise SystemExit(f"{path} exists - refusing to overwrite evidence")
    path.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps({k: v for k, v in report.items() if k != "by_province"}, ensure_ascii=False, indent=2))
    print(json.dumps(report["by_province"], ensure_ascii=False, indent=2))


def assign_provinces(sources: Path, rows: list[Any]) -> dict[str, list[dict[str, Any]]]:
    """Province of each point from the admin_level=4 polygons of the locked export."""
    settings = get_settings()
    engine = create_engine(settings.database_url)
    provs = []
    with (sources / "admin_boundaries.geojsonseq").open(encoding="utf-8") as fh:
        for raw in fh:
            raw = raw.strip().lstrip("\x1e")
            if raw:
                f = json.loads(raw)
                p = f["properties"]
                if p.get("@type") == "relation" and p.get("admin_level") == "4":
                    provs.append({"name": p["name"], "g": json.dumps(f["geometry"])})
    out: dict[str, list[dict[str, Any]]] = defaultdict(list)
    with engine.begin() as conn:
        conn.execute(text("CREATE TEMP TABLE prov (name text, g geometry)"))
        conn.execute(text("INSERT INTO prov SELECT :name, ST_MakeValid(ST_SetSRID(ST_GeomFromGeoJSON(:g), 4326))"), provs)
        conn.execute(text("CREATE INDEX ON prov USING gist (g)"))
        conn.execute(text("CREATE TEMP TABLE pt (id bigint, cat text, x float8, y float8)"))
        conn.execute(text("INSERT INTO pt VALUES (:id, :cat, :x, :y)"),
                     [{"id": r["id"], "cat": r["cat"], "x": r["x"], "y": r["y"]} for r in rows])
        # The snapshot still carries some pre-2025 / "... cũ" province relations that overlap
        # the merged provinces: each point gets exactly one province - the largest containing
        # relation (a merged province contains its former parts), never a "cũ" one.
        for pid, cat, x, y, name in conn.execute(text("""SELECT DISTINCT ON (pt.id) pt.id, pt.cat, pt.x, pt.y, prov.name
                FROM pt JOIN prov ON ST_Intersects(prov.g, ST_SetSRID(ST_MakePoint(pt.x, pt.y), 4326))
                WHERE prov.name NOT LIKE '%% cũ'
                ORDER BY pt.id, ST_Area(prov.g) DESC""")).all():
            out[name].append({"id": pid, "cat": cat, "x": x, "y": y, "province": name})
    return out


if __name__ == "__main__":
    main()
