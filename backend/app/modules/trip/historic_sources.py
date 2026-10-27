"""GEO-A: compare candidate sources for the boundary of the former Thị trấn Đông Anh
(pre-2025) with the OSM historic relation 17627914 of the locked snapshot.

Report only. Nothing here changes a service-area version or a classification; a
source becomes usable only by an explicit owner decision. Third-party geometry
(e.g. GADM, redistribution restricted) is read from a local path and never
written out - only metrics are.

Run (compose):
  docker compose --profile service-area run --rm -v <dir with gadm41_VNM_3.json>:/ext:ro \
    service-area-build python -m app.modules.trip.historic_sources --gadm /ext/gadm41_VNM_3.json \
    --version <service_area_version>
"""

import argparse
import hashlib
import json
from pathlib import Path
from typing import Any

from sqlalchemy import create_engine, text

from app.core.settings import get_settings

RELATION = 17627914
TOWN_NODE = 13799910539          # OSM place=town "Đông Anh" (in today's Xã Phúc Thịnh)
AREA_BBOX = (105.75, 21.05, 105.95, 21.25)  # current communes considered for the split
UTM = 32648                      # metric CRS for Hà Nội
SCHEMA = "hist_cmp"


def osm_member_ways(sources: Path) -> list[dict[str, Any]]:
    members: list[int] = []
    for line in (sources / "historic_relations.opl").read_text(encoding="utf-8").splitlines():
        if line.startswith(f"r{RELATION} "):
            members = [int(m[1:].split("@")[0]) for m in line.rsplit(" M", 1)[1].split(",") if m.startswith("w")]
    ways = []
    with (sources / "historic_member_ways.geojsonseq").open(encoding="utf-8") as fh:
        for raw in fh:
            raw = raw.strip().lstrip("\x1e")
            if raw:
                f = json.loads(raw)
                if f["properties"].get("@type") == "way" and f["properties"]["@id"] in members:
                    ways.append({"id": f["properties"]["@id"], "g": json.dumps(f["geometry"])})
    return ways


def iter_features(path: Path) -> Any:
    with path.open(encoding="utf-8") as fh:
        for raw in fh:
            raw = raw.strip().lstrip("")
            if raw:
                yield json.loads(raw)


def town_node(sources: Path) -> tuple[float, float]:
    for f in iter_features(sources / "places.geojsonseq"):
        if f["properties"].get("@type") == "node" and f["properties"]["@id"] == TOWN_NODE:
            return tuple(f["geometry"]["coordinates"])  # type: ignore[return-value]
    raise SystemExit(f"node/{TOWN_NODE} not in places export")


def current_units(sources: Path) -> list[dict[str, str]]:
    """Today's level-6 units with a vertex inside AREA_BBOX (from the same locked export)."""
    x0, y0, x1, y1 = AREA_BBOX
    out = []
    for f in iter_features(sources / "admin_boundaries.geojsonseq"):
        p = f["properties"]
        if p.get("admin_level") != "6" or p.get("@type") != "relation":
            continue
        g = f["geometry"]
        polys = g["coordinates"] if g["type"] == "MultiPolygon" else [g["coordinates"]]
        if any(x0 <= x <= x1 and y0 <= y <= y1 for poly in polys for ring in poly for x, y in ring):
            out.append({"name": p["name"], "g": json.dumps(g)})
    return out


def gadm_town(path: Path) -> tuple[dict[str, Any], str]:
    data = json.loads(path.read_text(encoding="utf-8"))
    hits = [f for f in data["features"] if f["properties"].get("NAME_2") == "ĐôngAnh"
            and f["properties"].get("TYPE_3") == "Thịtrấn"]
    if len(hits) != 1:
        raise SystemExit(f"expected one GADM feature for Thị trấn Đông Anh, found {len(hits)}")
    return hits[0], hashlib.sha256(path.read_bytes()).hexdigest()


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--gadm", type=Path, required=True)
    parser.add_argument("--version", required=True)
    parser.add_argument("--sources", type=Path, default=Path("/osm/service_area"))
    parser.add_argument("--out", type=Path, default=Path("/out"))
    args = parser.parse_args()

    ways = osm_member_ways(args.sources)
    feature, gadm_sha = gadm_town(args.gadm)
    node_xy = town_node(args.sources)
    units = current_units(args.sources)
    engine = create_engine(get_settings().database_url)
    with engine.begin() as conn:
        conn.execute(text(f"DROP SCHEMA IF EXISTS {SCHEMA} CASCADE"))
        conn.execute(text(f"CREATE SCHEMA {SCHEMA}"))
        conn.execute(text(f"CREATE TABLE {SCHEMA}.osm (id bigint, g geometry(LineString, {UTM}))"))
        conn.execute(text(f"INSERT INTO {SCHEMA}.osm SELECT :id, ST_Transform(ST_SetSRID(ST_GeomFromGeoJSON(:g), 4326), {UTM})"),
                     ways)
        conn.execute(text(f"CREATE TABLE {SCHEMA}.units (name text, g geometry(MultiPolygon, {UTM}))"))
        conn.execute(text(f"""INSERT INTO {SCHEMA}.units SELECT :name, ST_Transform(ST_Multi(ST_CollectionExtract(
            ST_MakeValid(ST_SetSRID(ST_GeomFromGeoJSON(:g), 4326)), 3)), {UTM})"""), units)
        conn.execute(text(f"""CREATE TABLE {SCHEMA}.gadm AS SELECT ST_Transform(ST_Multi(ST_MakeValid(
            ST_SetSRID(ST_GeomFromGeoJSON(:g), 4326))), {UTM}) AS g"""), {"g": json.dumps(feature["geometry"])})
        m = conn.execute(text(f"""
            WITH chain AS (SELECT ST_LineMerge(ST_Collect(g)) AS g FROM {SCHEMA}.osm),
                 pts AS (SELECT (ST_Dump(ST_LineInterpolatePoints(o.g, LEAST(1.0, 25.0 / ST_Length(o.g)), true))).geom AS p
                         FROM {SCHEMA}.osm o),
                 d AS (SELECT ST_Distance(p, ST_Boundary(a.g)) AS dist FROM pts, {SCHEMA}.gadm a)
            SELECT (SELECT ST_Length(g) / 1000 FROM chain) AS osm_km,
                   (SELECT ST_IsClosed(g) FROM chain) AS osm_closed,
                   (SELECT ST_Distance(ST_StartPoint(g), ST_EndPoint(g)) FROM chain) AS osm_gap_m,
                   (SELECT ST_Area(g) / 1e6 FROM {SCHEMA}.gadm) AS gadm_km2,
                   (SELECT ST_NPoints(g) FROM {SCHEMA}.gadm) AS gadm_vertices,
                   (SELECT ST_Length(ST_Boundary(g)) / 1000 FROM {SCHEMA}.gadm) AS gadm_perimeter_km,
                   (SELECT count(*) FROM d) AS samples,
                   (SELECT percentile_cont(0.5) WITHIN GROUP (ORDER BY dist) FROM d) AS median_m,
                   (SELECT percentile_cont(0.95) WITHIN GROUP (ORDER BY dist) FROM d) AS p95_m,
                   (SELECT max(dist) FROM d) AS max_m,
                   (SELECT ST_Length(ST_Difference(ST_Boundary(a.g), ST_Buffer(c.g, 100))) / 1000
                    FROM {SCHEMA}.gadm a, chain c) AS gadm_boundary_not_near_osm_km""")).mappings().one()
        split = conn.execute(text(f"""SELECT u.name, ST_Area(ST_Intersection(u.g, a.g)) / 1e6 AS km2
            FROM {SCHEMA}.units u, {SCHEMA}.gadm a WHERE ST_Intersects(u.g, a.g) ORDER BY 2 DESC""")).mappings().all()
        town = conn.execute(text(f"""SELECT ST_Contains(a.g, ST_Transform(ST_SetSRID(ST_MakePoint(:x, :y), 4326), {UTM}))
            FROM {SCHEMA}.gadm a"""), {"x": node_xy[0], "y": node_xy[1]}).scalar_one()
        urban_overlap = conn.execute(text(f"""SELECT ST_Area(ST_Intersection(ST_Transform(u.geom, {UTM}), a.g)) / 1e6
            FROM service_areas u, {SCHEMA}.gadm a WHERE u.service_area_version = :v AND u.area_type = 'URBAN'"""),
            {"v": args.version}).scalar_one()
        conn.execute(text(f"DROP SCHEMA {SCHEMA} CASCADE"))

    report = {
        "relation": f"relation/{RELATION}", "service_area_version": args.version,
        "osm": {"member_ways": len(ways), "length_km": round(m["osm_km"], 3), "closed": m["osm_closed"],
                "open_ring_gap_m": round(m["osm_gap_m"], 1)},
        "gadm": {"dataset": "GADM 4.1 gadm41_VNM_3.json (level 3, pre-2025 units)", "sha256": gadm_sha,
                 "gid": feature["properties"]["GID_3"], "area_km2": round(m["gadm_km2"], 3),
                 "vertices": m["gadm_vertices"], "perimeter_km": round(m["gadm_perimeter_km"], 3),
                 "contains_osm_town_node": town,
                 "split_over_current_units_km2": {r["name"]: round(r["km2"], 3) for r in split if r["km2"] >= 0.01},
                 "overlap_with_current_urban_km2": round(urban_overlap, 3)},
        "deviation_osm_to_gadm_boundary_m": {"samples_every_25m": m["samples"], "median": round(m["median_m"], 1),
                                             "p95": round(m["p95_m"], 1), "max": round(m["max_m"], 1)},
        "gadm_boundary_farther_than_100m_from_osm_km": round(m["gadm_boundary_not_near_osm_km"], 3),
    }
    (args.out / "historic_sources_dong_anh.json").write_text(json.dumps(report, ensure_ascii=False, indent=2),
                                                             encoding="utf-8")
    print(json.dumps(report, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
