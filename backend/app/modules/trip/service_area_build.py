"""Build CANDIDATE urban_service_area / total_service_area geometries
(owner decisions P1-D1 / P1-D3; Revision 9 Section 2.3).

Inputs  : OSM exports from scripts/osm/export_service_area_sources.sh (+ MANIFEST),
          config/service_area_rules.candidate.yaml, baseline max_total_service_radius_km,
          OSRM car (road distance from the anchor).
Outputs : rows in `service_areas` with status CANDIDATE (never APPROVED), and a
          review bundle in <out>/<service_area_version>/:
          urban.geojson, total.geojson, units.csv, report.json, REVIEW.md

Deterministic: identical inputs give the identical service_area_version and
geometry; a rerun reports "unchanged" and a changed geometry under an existing
version aborts.

Run (compose): docker compose --profile service-area run --rm service-area-build
"""

import argparse
import csv
import hashlib
import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import httpx
import yaml
from sqlalchemy import Connection, create_engine, text

from app.core.config_baseline import get_config_baseline
from app.core.settings import get_settings

SCHEMA = "sa_build"  # transient working schema, dropped at the end of a run
OSRM_BATCH = 150     # destinations per /table call (server max-table-size is 200)


@dataclass
class Build:
    manifest: dict[str, str]
    rules: dict[str, Any]
    max_km: float
    log: list[str] = field(default_factory=list)
    conflicts: list[str] = field(default_factory=list)

    def note(self, msg: str) -> None:
        print(f"[service-area-build] {msg}")
        self.log.append(msg)


def read_manifest(path: Path) -> dict[str, str]:
    out = {}
    for line in path.read_text(encoding="utf-8").splitlines():
        if ": " in line:
            key, value = line.split(": ", 1)
            out[key.strip()] = value.strip()
    return out


def iter_geojsonseq(path: Path) -> Any:
    with path.open(encoding="utf-8") as fh:
        for line in fh:
            line = line.strip().lstrip("\x1e")
            if line:
                yield json.loads(line)


# --- loading -----------------------------------------------------------------------


def load_inputs(conn: Connection, sources: Path, b: Build) -> None:
    conn.execute(text(f"DROP SCHEMA IF EXISTS {SCHEMA} CASCADE"))
    conn.execute(text(f"CREATE SCHEMA {SCHEMA}"))
    conn.execute(text(f"""CREATE TABLE {SCHEMA}.units (
        osm_id bigint PRIMARY KEY, admin_level int NOT NULL, name text NOT NULL, iso text,
        input_valid boolean NOT NULL, geom geometry(MultiPolygon, 4326) NOT NULL)"""))
    conn.execute(text(f"""CREATE TABLE {SCHEMA}.places (
        osm_type text NOT NULL, osm_id bigint NOT NULL, name text, place text, amenity text,
        geom geometry(Point, 4326) NOT NULL, PRIMARY KEY (osm_type, osm_id))"""))

    rows = []
    for f in iter_geojsonseq(sources / "admin_boundaries.geojsonseq"):
        p = f["properties"]
        if p.get("@type") != "relation" or p.get("boundary") != "administrative":
            continue
        if p.get("admin_level") not in ("4", "6") or not p.get("name"):
            continue
        rows.append({"id": p["@id"], "lvl": int(p["admin_level"]), "name": p["name"],
                     "iso": p.get("ISO3166-2"), "g": json.dumps(f["geometry"])})
    conn.execute(text(f"""INSERT INTO {SCHEMA}.units (osm_id, admin_level, name, iso, input_valid, geom)
        SELECT :id, :lvl, :name, :iso, ST_IsValid(g),
               ST_Multi(ST_CollectionExtract(ST_MakeValid(g), 3))
        FROM (SELECT ST_SetSRID(ST_GeomFromGeoJSON(:g), 4326) AS g) s
        ON CONFLICT (osm_id) DO NOTHING"""), rows)
    counts = conn.execute(text(
        f"SELECT admin_level, count(*), count(*) FILTER (WHERE NOT input_valid) FROM {SCHEMA}.units GROUP BY 1 ORDER BY 1"
    )).all()
    b.note("loaded admin units: " + ", ".join(f"level {lvl}: {n} ({bad} repaired with ST_MakeValid)" for lvl, n, bad in counts))

    places = []
    for f in iter_geojsonseq(sources / "places.geojsonseq"):
        p = f["properties"]
        places.append({"t": p["@type"], "id": p["@id"], "name": p.get("name"), "place": p.get("place"),
                       "amenity": p.get("amenity"), "g": json.dumps(f["geometry"])})
    conn.execute(text(f"""INSERT INTO {SCHEMA}.places (osm_type, osm_id, name, place, amenity, geom)
        SELECT :t, :id, :name, :place, :amenity, ST_PointOnSurface(ST_MakeValid(ST_SetSRID(ST_GeomFromGeoJSON(:g), 4326)))
        ON CONFLICT DO NOTHING"""), places)
    b.note(f"loaded places: {len(places)}")


# --- selection ---------------------------------------------------------------------


def province_containing(conn: Connection, point_sql: str, params: dict[str, Any]) -> list[Any]:
    return conn.execute(text(f"""SELECT u.osm_id, u.name, u.iso FROM {SCHEMA}.units u
        WHERE u.admin_level = 4 AND ST_Intersects(u.geom, ({point_sql}))"""), params).all()


def node_point_sql() -> str:
    return f"SELECT geom FROM {SCHEMA}.places WHERE osm_type = 'node' AND osm_id = :node"


def select_city(conn: Connection, b: Build) -> Any:
    iso = b.rules["city"]["iso3166_2"]
    rows = conn.execute(text(f"SELECT osm_id, name, iso FROM {SCHEMA}.units WHERE admin_level = 4 AND iso = :iso"),
                        {"iso": iso}).all()
    if len(rows) != 1:
        raise SystemExit(f"expected exactly one admin_level=4 unit with ISO3166-2={iso}, found {len(rows)}")
    b.note(f"city: r{rows[0].osm_id} {rows[0].name} ({iso})")
    return rows[0]


def units_in_provinces(conn: Connection, province_ids: list[int]) -> list[Any]:
    return conn.execute(text(f"""SELECT u.osm_id, u.name, p.osm_id AS province_id, p.name AS province,
            ST_X(ST_PointOnSurface(u.geom)) AS lon, ST_Y(ST_PointOnSurface(u.geom)) AS lat
        FROM {SCHEMA}.units u JOIN {SCHEMA}.units p
          ON p.admin_level = 4 AND ST_Intersects(p.geom, ST_PointOnSurface(u.geom))
        WHERE u.admin_level = 6 AND p.osm_id = ANY(:ids)
        ORDER BY u.osm_id"""), {"ids": province_ids}).all()


def select_urban(conn: Connection, city: Any, b: Build) -> list[dict[str, Any]]:
    rules = b.rules["urban"]
    units = units_in_provinces(conn, [city.osm_id])
    chosen: dict[int, dict[str, Any]] = {}
    if rules.get("include_city_wards"):
        for u in units:
            if u.name.startswith("Phường "):
                chosen[u.osm_id] = {"osm_id": u.osm_id, "name": u.name, "province": u.province, "rule": "U1 city ward"}
    for wanted in rules.get("include_city_communes_named", []):
        matches = [u for u in units if u.name == wanted]
        if len(matches) != 1:
            b.conflicts.append(f"urban rule U2: '{wanted}' matched {len(matches)} units inside the city (expected 1)")
        for u in matches:
            chosen[u.osm_id] = {"osm_id": u.osm_id, "name": u.name, "province": u.province, "rule": "U2 named commune"}
    b.note(f"urban: {len(units)} level-6 units in city, selected {len(chosen)}")
    return sorted(chosen.values(), key=lambda r: r["osm_id"])


def select_provinces(conn: Connection, city: Any, b: Build) -> list[dict[str, Any]]:
    provinces = [{"neighbour": "(city)", "osm_id": city.osm_id, "name": city.name, "iso": city.iso, "evidence": "city"}]
    for n in b.rules["total"]["neighbours"]:
        if n["by"] == "province_iso":
            rows = conn.execute(text(f"SELECT osm_id, name, iso FROM {SCHEMA}.units WHERE admin_level = 4 AND iso = :iso"),
                                {"iso": n["iso3166_2"]}).all()
            evidence = f"admin_level=4 unit with ISO3166-2={n['iso3166_2']}"
        else:
            rows = province_containing(conn, node_point_sql(), {"node": n["osm_node"]})
            evidence = f"admin_level=4 unit containing node/{n['osm_node']}"
        if len(rows) != 1:
            b.conflicts.append(f"neighbour '{n['name']}': {evidence} matched {len(rows)} provinces (expected 1)")
            continue
        r = rows[0]
        provinces.append({"neighbour": n["name"], "osm_id": r.osm_id, "name": r.name, "iso": r.iso, "evidence": evidence})
    unique: dict[int, dict[str, Any]] = {}
    for p in provinces:
        unique.setdefault(p["osm_id"], p | {"neighbours": []})["neighbours"].append(p["neighbour"])
    b.note("provinces for total area: " + "; ".join(f"{p['name']} <- {', '.join(p['neighbours'])}" for p in unique.values()))
    return list(unique.values())


def road_distances(osrm_url: str, anchor: tuple[float, float], points: list[tuple[float, float]]) -> list[tuple[float | None, float]]:
    """(road km from the anchor or None if unroutable, snap distance m) per point."""
    out: list[tuple[float | None, float]] = []
    for i in range(0, len(points), OSRM_BATCH):
        batch = points[i:i + OSRM_BATCH]
        coords = ";".join(f"{lon:.6f},{lat:.6f}" for lon, lat in [anchor, *batch])
        resp = httpx.get(f"{osrm_url}/table/v1/driving/{coords}",
                         params={"sources": "0", "annotations": "distance"},
                         headers={"Connection": "close"}, timeout=60)
        body = resp.json()
        if resp.status_code != 200 or body.get("code") != "Ok":
            raise SystemExit(f"OSRM table failed: HTTP {resp.status_code} {body.get('code')} {body.get('message')}")
        for j, dist in enumerate(body["distances"][0][1:]):
            out.append((None if dist is None else dist / 1000, body["destinations"][j + 1]["distance"]))
    return out


def select_total(conn: Connection, provinces: list[dict[str, Any]], osrm_url: str, b: Build) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    anchor_id = b.rules["total"]["anchor"]["osm_node"]
    anchor = conn.execute(text(f"SELECT ST_X(geom), ST_Y(geom), name FROM {SCHEMA}.places WHERE osm_type='node' AND osm_id=:n"),
                          {"n": anchor_id}).one_or_none()
    if anchor is None:
        raise SystemExit(f"anchor node/{anchor_id} not found in places export")
    b.note(f"anchor: node/{anchor_id} '{anchor[2]}' ({anchor[0]:.5f}, {anchor[1]:.5f}) - ANCHOR_DEFINITION_REQUIRED")

    all_provinces = conn.execute(text(f"SELECT osm_id FROM {SCHEMA}.units WHERE admin_level = 4")).scalars().all()
    selected_ids = {p["osm_id"] for p in provinces}
    # The routing graph only covers the P0 clip bbox; a unit outside it cannot be
    # routed (OSRM would snap it to the bbox edge), so it is excluded and reported.
    min_lon, min_lat, max_lon, max_lat = (float(x) for x in b.manifest["bbox"].split(","))
    units, outside_extract = [], {}
    for u in units_in_provinces(conn, list(all_provinces)):
        if min_lon <= u.lon <= max_lon and min_lat <= u.lat <= max_lat:
            units.append(u)
        elif u.province_id in selected_ids:
            outside_extract[u.province] = outside_extract.get(u.province, 0) + 1
    dists = road_distances(osrm_url, (anchor[0], anchor[1]), [(u.lon, u.lat) for u in units])
    chosen, outside_scope = [], {}
    unreachable = 0
    for u, (km, snap_m) in zip(units, dists, strict=True):
        if km is None:
            unreachable += u.province_id in selected_ids
            continue
        if km > b.max_km:
            continue
        row = {"osm_id": u.osm_id, "name": u.name, "province": u.province, "road_km": round(km, 3),
               "snap_m": round(snap_m, 1), "rule": f"T road distance <= {b.max_km} km"}
        if u.province_id in selected_ids:
            chosen.append(row)
        else:
            outside_scope.setdefault(u.province, 0)
            outside_scope[u.province] += 1
    b.note(f"total: {len(chosen)} level-6 units within {b.max_km} km in selected provinces; "
           f"{unreachable} unroutable; excluded as outside the routing extract: {outside_extract or 'none'}; "
           f"other provinces with units in range: {outside_scope or 'none'}")
    stats = {"anchor": {"osm_node": anchor_id, "name": anchor[2], "lon": anchor[0], "lat": anchor[1]},
             "units_routed": len(units), "unroutable_in_scope": unreachable,
             "excluded_outside_routing_extract": outside_extract,
             "units_in_range_outside_listed_provinces": outside_scope}
    return sorted(chosen, key=lambda r: r["osm_id"]), stats


# --- geometry, checks, persistence ---------------------------------------------------


def union_sql(ids_param: str) -> str:
    return (f"SELECT ST_Multi(ST_CollectionExtract(ST_MakeValid(ST_Union(geom)), 3)) FROM {SCHEMA}.units "
            f"WHERE osm_id = ANY(:{ids_param})")


def geometry_checks(conn: Connection, urban_ids: list[int], total_ids: list[int]) -> dict[str, Any]:
    row = conn.execute(text(f"""WITH u AS ({union_sql('u')}), t AS ({union_sql('t')})
        SELECT ST_IsValid((SELECT * FROM u)) AS urban_valid, ST_IsValid((SELECT * FROM t)) AS total_valid,
               ST_NumGeometries((SELECT * FROM u)) AS urban_parts, ST_NumGeometries((SELECT * FROM t)) AS total_parts,
               ST_Area((SELECT * FROM u)::geography) / 1e6 AS urban_km2, ST_Area((SELECT * FROM t)::geography) / 1e6 AS total_km2,
               ST_CoveredBy((SELECT * FROM u), (SELECT * FROM t)) AS urban_within_total,
               (SELECT sum(ST_Area(geom::geography)) / 1e6 FROM {SCHEMA}.units WHERE osm_id = ANY(:u)) AS urban_units_km2,
               (SELECT sum(ST_Area(geom::geography)) / 1e6 FROM {SCHEMA}.units WHERE osm_id = ANY(:t)) AS total_units_km2
    """), {"u": urban_ids, "t": total_ids}).mappings().one()
    checks = dict(row)
    # Overlap between selected units = sum of unit areas - area of their union.
    checks["urban_overlap_km2"] = checks["urban_units_km2"] - checks["urban_km2"]
    checks["total_overlap_km2"] = checks["total_units_km2"] - checks["total_km2"]
    return {k: (round(v, 4) if isinstance(v, float) else v) for k, v in checks.items()}


def compute_version(b: Build, urban_ids: list[int], total_ids: list[int], anchor_id: int) -> str:
    material = {
        "manifest": b.manifest,  # source/routing extract MD5s, export MD5s, bbox
        "rules": b.rules,
        "max_total_service_radius_km": b.max_km,
        "anchor": anchor_id,
        "urban_unit_ids": urban_ids,
        "total_unit_ids": total_ids,
    }
    digest = hashlib.sha256(json.dumps(material, sort_keys=True, ensure_ascii=False).encode()).hexdigest()
    return f"sa-cand-{digest[:12]}"


def persist(conn: Connection, version: str, area_type: str, ids: list[int], source: dict[str, Any], b: Build) -> str:
    inserted = conn.execute(text(f"""INSERT INTO public.service_areas (area_type, service_area_version, status, geom, source_json)
        SELECT :area_type, :version, 'CANDIDATE', ({union_sql('ids')}), CAST(:source AS jsonb)
        ON CONFLICT (area_type, service_area_version) DO NOTHING"""),
        {"area_type": area_type, "version": version, "ids": ids, "source": json.dumps(source, ensure_ascii=False)}).rowcount
    if inserted:
        return "inserted"
    same = conn.execute(text(f"""SELECT ST_Equals(geom, ({union_sql('ids')})) FROM public.service_areas
        WHERE area_type = :area_type AND service_area_version = :version"""),
        {"area_type": area_type, "version": version, "ids": ids}).scalar_one()
    if not same:
        raise SystemExit(f"{area_type} {version} already stored with a different geometry - import is not stable")
    return "unchanged (ST_Equals)"


def check_locations(conn: Connection, version: str, b: Build) -> list[dict[str, Any]]:
    results = []
    for loc in b.rules.get("test_locations", []):
        row: dict[str, Any] = {"label": loc["label"], "osm": loc.get("osm"), "source": loc.get("source"),
                               "expected_urban": loc.get("expected_urban"), "expected_total": loc.get("expected_total")}
        if not loc.get("osm"):
            row |= {"result": "UNRESOLVED", "detail": loc.get("note", "no OSM object")}
            results.append(row)
            continue
        osm_type, osm_id = loc["osm"].split("/")
        hit = conn.execute(text(f"""SELECT ST_X(p.geom) AS lon, ST_Y(p.geom) AS lat,
                (SELECT name FROM {SCHEMA}.units u WHERE u.admin_level = 6 AND ST_Intersects(u.geom, p.geom) LIMIT 1) AS unit,
                (SELECT name FROM {SCHEMA}.units u WHERE u.admin_level = 4 AND ST_Intersects(u.geom, p.geom) LIMIT 1) AS province,
                (SELECT ST_Intersects(geom, p.geom) FROM public.service_areas WHERE area_type='URBAN' AND service_area_version=:v) AS in_urban,
                (SELECT ST_Intersects(geom, p.geom) FROM public.service_areas WHERE area_type='TOTAL' AND service_area_version=:v) AS in_total
            FROM {SCHEMA}.places p WHERE p.osm_type = :t AND p.osm_id = :id"""),
            {"t": osm_type, "id": int(osm_id), "v": version}).mappings().one_or_none()
        if hit is None:
            row |= {"result": "UNRESOLVED", "detail": f"{loc['osm']} not in places export"}
        else:
            row |= dict(hit)
            mismatches = []
            if loc.get("expected_urban") is not None and hit["in_urban"] != loc["expected_urban"]:
                mismatches.append("urban")
            if loc.get("expected_total") is not None and hit["in_total"] != loc["expected_total"]:
                mismatches.append("total")
            row["result"] = "MISMATCH(" + ",".join(mismatches) + ")" if mismatches else "AS_EXPECTED"
            if loc.get("note"):
                row["detail"] = loc["note"]
        results.append(row)
    return results


def write_bundle(conn: Connection, out: Path, version: str, report: dict[str, Any],
                 urban: list[dict[str, Any]], total: list[dict[str, Any]]) -> None:
    out.mkdir(parents=True, exist_ok=True)
    for area_type, name in (("URBAN", "urban"), ("TOTAL", "total")):
        geom = conn.execute(text("""SELECT ST_AsGeoJSON(geom, 6) FROM public.service_areas
            WHERE area_type = :a AND service_area_version = :v"""), {"a": area_type, "v": version}).scalar_one()
        fc = {"type": "FeatureCollection", "features": [{"type": "Feature", "geometry": json.loads(geom), "properties": {
            "area_type": area_type, "service_area_version": version, "status": "CANDIDATE",
            "approval": "PENDING_OWNER_APPROVAL"}}]}
        (out / f"{name}.geojson").write_text(json.dumps(fc, ensure_ascii=False), encoding="utf-8")
    with (out / "units.csv").open("w", newline="", encoding="utf-8") as fh:
        w = csv.DictWriter(fh, fieldnames=["area_type", "osm_relation", "name", "province", "rule", "road_km", "snap_m"])
        w.writeheader()
        for area_type, rows in (("URBAN", urban), ("TOTAL", total)):
            for r in rows:
                w.writerow({"area_type": area_type, "osm_relation": r["osm_id"], "name": r["name"], "province": r["province"],
                            "rule": r["rule"], "road_km": r.get("road_km", ""), "snap_m": r.get("snap_m", "")})
    (out / "report.json").write_text(json.dumps(report, ensure_ascii=False, indent=2, default=str), encoding="utf-8")
    (out / "REVIEW.md").write_text(render_review(report), encoding="utf-8")


def render_review(r: dict[str, Any]) -> str:
    c = r["checks"]
    lines = [
        f"# Service-area candidate `{r['service_area_version']}` — review bundle",
        "",
        "**Status: CANDIDATE — PENDING_OWNER_APPROVAL (P1-D1 / P1-D3). Not GEOMETRY_APPROVED.**",
        "Generated by `app.modules.trip.service_area_build`; do not edit by hand (rerun instead).",
        "",
        "## 1. Selected units",
        f"- Urban: {len(r['urban_units'])} admin_level=6 units — full list in `units.csv` (area_type=URBAN).",
        f"- Total: {len(r['total_units'])} admin_level=6 units — full list in `units.csv` (area_type=TOTAL).",
        "- Urban units by rule: " + ", ".join(f"{k}: {v}" for k, v in r["urban_by_rule"].items()),
        "- Named communes (rule U2): " + ", ".join(u["name"] + f" (r{u['osm_id']})" for u in r["urban_units"] if u["rule"].startswith("U2")),
        "",
        "Provinces used for the total area:",
        "",
        "| Revision 9 name(s) | Current OSM unit | ISO | Evidence |",
        "|---|---|---|---|",
        *[f"| {', '.join(p['neighbours'])} | {p['name']} (r{p['osm_id']}) | {p['iso'] or ''} | {p['evidence']} |" for p in r["provinces"]],
        "",
        "## 2. Candidate GeoJSON",
        "`urban.geojson`, `total.geojson` (EPSG:4326, 6 decimals).",
        "",
        "## 3. OSM source and traceability",
        *[f"- {k}: `{v}`" for k, v in r["manifest"].items()],
        f"- rules file: `{r['rules_file']}` (rules_id `{r['rules']['rules_id']}`, status `{r['rules']['status']}`)",
        f"- max_total_service_radius_km (baseline): {r['max_km']}",
        "",
        "## 4. Polygon construction rules",
        "- Units are OSM `boundary=administrative` relations exported from the unclipped Geofabrik source "
        "(the P0 bbox clip leaves boundary relations that cross the bbox incomplete); geometry repaired with `ST_MakeValid`, polygons only.",
        "- Units whose `ST_PointOnSurface` lies outside the routing-extract bbox are not routed and are excluded from the total area.",
        "- A unit belongs to a province when its `ST_PointOnSurface` lies in the province polygon.",
        "- **Urban**: U1 = every `Phường …` unit of the city; U2 = the communes listed in the rules, matched by exact name inside the city.",
        f"- **Total**: units of the listed provinces whose `ST_PointOnSurface` is within {r['max_km']} km by OSRM car road distance from the anchor "
        f"(node/{r['total_stats']['anchor']['osm_node']} '{r['total_stats']['anchor']['name']}'). **ANCHOR_DEFINITION_REQUIRED.**",
        "- Area = `ST_Union` of the selected units.",
        "",
        "Geometry checks:",
        "",
        "| Check | Value |",
        "|---|---|",
        *[f"| {k} | {v} |" for k, v in c.items()],
        "",
        "## 5. Boundary locations",
        "",
        "| Location | OSM | Expected urban | Actual urban | In total | Containing unit / province | Result |",
        "|---|---|---|---|---|---|---|",
        *[f"| {t['label']} | {t.get('osm') or '—'} | {t.get('expected_urban')} | {t.get('in_urban', '—')} | {t.get('in_total', '—')} | "
          f"{t.get('unit', '—')} / {t.get('province', '—')} | **{t['result']}** {t.get('detail', '')} |" for t in r["locations"]],
        "",
        "## 6. service_area_version",
        "`sa-cand-` + first 12 hex of SHA-256 over: the export MANIFEST (source and routing-extract MD5s, export MD5s, bbox), the parsed rules, "
        "max_total_service_radius_km, anchor, and the sorted selected unit ids. "
        "Same inputs → same version; a rerun verifies the stored geometry with `ST_Equals`.",
        f"- This run: `{r['service_area_version']}`; persistence: {r['persist']}",
        "",
        "## 7. Open conflicts / insufficient data",
        *([f"- {x}" for x in r["conflicts"]] or ["- none detected by the pipeline"]),
        f"- Units in range of the anchor but in provinces not listed in Section 1: {r['total_stats']['units_in_range_outside_listed_provinces'] or 'none'}",
        f"- Units of listed provinces excluded because they lie outside the routing extract bbox: {r['total_stats']['excluded_outside_routing_extract'] or 'none'}",
        "",
    ]
    return "\n".join(lines)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--sources", type=Path, default=Path("/osm/service_area"))
    parser.add_argument("--rules", type=Path, default=Path("/app/config/service_area_rules.candidate.yaml"))
    parser.add_argument("--out", type=Path, default=Path("/out"))
    args = parser.parse_args()

    settings = get_settings()
    rules = yaml.safe_load(args.rules.read_text(encoding="utf-8"))
    b = Build(manifest=read_manifest(args.sources / "MANIFEST"), rules=rules,
              max_km=float(get_config_baseline()["spatial_and_service_areas"]["max_total_service_radius_km"]))

    engine = create_engine(settings.database_url)
    with engine.begin() as conn:
        load_inputs(conn, args.sources, b)
        city = select_city(conn, b)
        urban = select_urban(conn, city, b)
        provinces = select_provinces(conn, city, b)
        total, total_stats = select_total(conn, provinces, settings.osrm_car_url, b)
        urban_ids = [u["osm_id"] for u in urban]
        total_ids = [t["osm_id"] for t in total]
        missing = sorted(set(urban_ids) - set(total_ids))
        if missing:
            b.conflicts.append(f"{len(missing)} urban units are not in the total area (road distance rule): {missing}")
        version = compute_version(b, urban_ids, total_ids, rules["total"]["anchor"]["osm_node"])
        source = {"manifest": b.manifest, "rules_id": rules["rules_id"], "rules_status": rules["status"]}
        persist_result = {
            "URBAN": persist(conn, version, "URBAN", urban_ids, source, b),
            "TOTAL": persist(conn, version, "TOTAL", total_ids, source, b),
        }
        checks = geometry_checks(conn, urban_ids, total_ids)
        if not checks["urban_within_total"]:
            b.conflicts.append("urban area is not fully covered by the total area")
        for area in ("urban", "total"):
            if checks[f"{area}_parts"] > 1:
                b.conflicts.append(f"{area} area consists of {checks[f'{area}_parts']} disjoint polygons "
                                   "(selected units are not contiguous)")
        locations = check_locations(conn, version, b)
        for loc in locations:
            if loc["result"] != "AS_EXPECTED":
                b.conflicts.append(f"location '{loc['label']}' ({loc.get('osm') or 'no OSM object'}): {loc['result']}"
                                   + (f" - in {loc['unit']}" if loc.get("unit") else "")
                                   + (f" - {loc['detail']}" if loc.get("detail") else ""))
        by_rule: dict[str, int] = {}
        for u in urban:
            by_rule[u["rule"]] = by_rule.get(u["rule"], 0) + 1
        report = {
            "service_area_version": version, "status": "CANDIDATE", "approval": "PENDING_OWNER_APPROVAL",
            "manifest": b.manifest, "rules_file": str(args.rules.name), "rules": rules, "max_km": b.max_km,
            "provinces": provinces, "urban_units": urban, "urban_by_rule": by_rule, "total_units": total,
            "total_stats": total_stats, "checks": checks, "locations": locations, "persist": persist_result,
            "conflicts": b.conflicts, "log": b.log,
        }
        write_bundle(conn, args.out / version, version, report, urban, total)
        conn.execute(text(f"DROP SCHEMA {SCHEMA} CASCADE"))
    b.note(f"service_area_version={version} persist={persist_result} -> {args.out / version}")


if __name__ == "__main__":
    main()
