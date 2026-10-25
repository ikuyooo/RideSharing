"""Build CANDIDATE urban_service_area / total_service_area geometries
(owner decisions P1-D1 / P1-D3 and "P1: GEOGRAPHY & S1 CLOSURE"; Revision 9 Section 2.3).

Inputs  : OSM exports from scripts/osm/export_service_area_sources.sh (+ MANIFEST),
          a rules file (config/service_area_rules.candidate*.yaml), baseline
          max_total_service_radius_km, OSRM car (road distance from the anchor).
Outputs : rows in `service_areas` with status CANDIDATE (never APPROVED), and a
          review bundle in <out>/<service_area_version>/:
          urban.geojson, total.geojson, units.csv, admin_mapping.csv,
          components.csv, sensitivity.csv, report.json, REVIEW.md, CHECKSUMS.sha256

Analyses (A4 150 km sensitivity, A6 component classification, A9 routing
coverage) only REPORT; they never modify the geometry.

Deterministic: identical inputs give the identical service_area_version and
geometry; a rerun reports "unchanged" and a changed geometry under an existing
version aborts.

Run (compose): docker compose --profile service-area run --rm service-area-build \
    python -m app.modules.trip.service_area_build --rules /app/config/<rules file>
"""

import argparse
import csv
import hashlib
import json
import re
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
# A6 analysis heuristics (classification only, not business rules).
SLIVER_MAX_KM2 = 0.01
SLIVER_MAX_GAP_M = 10.0


@dataclass
class Build:
    manifest: dict[str, str]
    rules: dict[str, Any]
    max_km: float
    bbox: tuple[float, float, float, float]
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


def envelope_sql(b: Build) -> str:
    return "ST_MakeEnvelope({}, {}, {}, {}, 4326)".format(*b.bbox)


# --- loading -----------------------------------------------------------------------


def load_inputs(conn: Connection, sources: Path, b: Build) -> None:
    conn.execute(text(f"DROP SCHEMA IF EXISTS {SCHEMA} CASCADE"))
    conn.execute(text(f"CREATE SCHEMA {SCHEMA}"))
    conn.execute(text(f"""CREATE TABLE {SCHEMA}.units (
        osm_id bigint PRIMARY KEY, admin_level int NOT NULL, name text NOT NULL, iso text,
        input_valid boolean NOT NULL, geom geometry(MultiPolygon, 4326) NOT NULL)"""))
    conn.execute(text(f"CREATE INDEX ON {SCHEMA}.units USING gist (geom)"))
    conn.execute(text(f"""CREATE TABLE {SCHEMA}.places (
        osm_type text NOT NULL, osm_id bigint NOT NULL, name text, kind text,
        geom_full geometry(Geometry, 4326) NOT NULL, geom geometry(Point, 4326) NOT NULL,
        PRIMARY KEY (osm_type, osm_id))"""))

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
        if f["geometry"]["type"] not in ("Point", "Polygon", "MultiPolygon"):
            continue  # closed ways are also exported as LineString; keep the area
        p = f["properties"]
        kind = next((f"{k}={p[k]}" for k in ("place", "amenity", "leisure", "landuse") if p.get(k)), None)
        places.append({"t": p["@type"], "id": p["@id"], "name": p.get("name"), "kind": kind,
                       "g": json.dumps(f["geometry"])})
    conn.execute(text(f"""INSERT INTO {SCHEMA}.places (osm_type, osm_id, name, kind, geom_full, geom)
        SELECT :t, :id, :name, :kind, g, ST_PointOnSurface(g)
        FROM (SELECT ST_MakeValid(ST_SetSRID(ST_GeomFromGeoJSON(:g), 4326)) AS g) s
        ON CONFLICT DO NOTHING"""), places)
    b.note(f"loaded places/landmarks: {len(places)}")


# --- selection ---------------------------------------------------------------------


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


def select_urban(conn: Connection, city: Any, b: Build) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
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
    areas = []
    for area in rules.get("include_osm_areas", []):
        osm_type, osm_id = area["osm"].split("/")
        row = conn.execute(text(f"""SELECT p.name, p.kind, ST_GeometryType(p.geom_full) AS gtype,
                ST_Area(ST_Intersection(p.geom_full, c.geom)::geography) / 1e6 AS km2_in_city,
                (SELECT u.name FROM {SCHEMA}.units u WHERE u.admin_level = 6 AND ST_Intersects(u.geom, p.geom) LIMIT 1) AS unit
            FROM {SCHEMA}.places p, {SCHEMA}.units c
            WHERE p.osm_type = :t AND p.osm_id = :id AND c.osm_id = :city"""),
            {"t": osm_type, "id": int(osm_id), "city": city.osm_id}).mappings().one_or_none()
        if row is None or row["gtype"] not in ("ST_Polygon", "ST_MultiPolygon") or not row["km2_in_city"]:
            b.conflicts.append(f"urban rule U3: {area['osm']} ({area.get('label')}) not found as a polygon inside the city")
            continue
        areas.append({"osm": area["osm"], "label": area.get("label"), "osm_name": row["name"], "kind": row["kind"],
                      "km2_in_city": round(row["km2_in_city"], 4), "containing_unit": row["unit"],
                      "rule": "U3 OSM urban-development polygon", "note": area.get("note")})
    b.note(f"urban: {len(units)} level-6 units in city, selected {len(chosen)} units + {len(areas)} OSM areas")
    return sorted(chosen.values(), key=lambda r: r["osm_id"]), areas


def map_neighbours(conn: Connection, city: Any, b: Build) -> list[dict[str, Any]]:
    provinces = [{"neighbour": "(city)", "osm_id": city.osm_id, "name": city.name, "iso": city.iso, "evidence": "city"}]
    for n in b.rules["total"]["neighbours"]:
        if n["by"] == "province_iso":
            rows = conn.execute(text(f"SELECT osm_id, name, iso FROM {SCHEMA}.units WHERE admin_level = 4 AND iso = :iso"),
                                {"iso": n["iso3166_2"]}).all()
            evidence = f"admin_level=4 unit with ISO3166-2={n['iso3166_2']}"
        else:
            rows = conn.execute(text(f"""SELECT u.osm_id, u.name, u.iso FROM {SCHEMA}.units u
                WHERE u.admin_level = 4 AND ST_Intersects(u.geom, ({node_point_sql()}))"""), {"node": n["osm_node"]}).all()
            evidence = f"admin_level=4 unit containing node/{n['osm_node']}"
        if len(rows) != 1:
            b.conflicts.append(f"neighbour '{n['name']}': {evidence} matched {len(rows)} provinces (expected 1)")
            continue
        r = rows[0]
        provinces.append({"neighbour": n["name"], "osm_id": r.osm_id, "name": r.name, "iso": r.iso, "evidence": evidence})
    unique: dict[int, dict[str, Any]] = {}
    for p in provinces:
        unique.setdefault(p["osm_id"], p | {"neighbours": []})["neighbours"].append(p["neighbour"])
    b.note("Section 1 neighbours -> provinces: " + "; ".join(f"{p['name']} <- {', '.join(p['neighbours'])}" for p in unique.values()))
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


def anchor_point(conn: Connection, b: Build) -> tuple[float, float, str]:
    anchor_id = b.rules["total"]["anchor"]["osm_node"]
    row = conn.execute(text(f"SELECT ST_X(geom), ST_Y(geom), name FROM {SCHEMA}.places WHERE osm_type='node' AND osm_id=:n"),
                       {"n": anchor_id}).one_or_none()
    if row is None:
        raise SystemExit(f"anchor node/{anchor_id} not found in places export")
    return float(row[0]), float(row[1]), str(row[2])


def select_total(conn: Connection, provinces: list[dict[str, Any]], osrm_url: str, b: Build
                 ) -> tuple[list[dict[str, Any]], dict[str, Any], dict[int, dict[str, Any]]]:
    lon, lat, name = anchor_point(conn, b)
    b.note(f"anchor: node/{b.rules['total']['anchor']['osm_node']} '{name}' ({lon:.5f}, {lat:.5f})")
    scope = b.rules["total"].get("province_scope", "listed")
    all_provinces = list(conn.execute(text(f"SELECT osm_id FROM {SCHEMA}.units WHERE admin_level = 4")).scalars())
    selected_ids = set(all_provinces) if scope == "all_within_range" else {p["osm_id"] for p in provinces}
    min_lon, min_lat, max_lon, max_lat = b.bbox
    routed, outside_extract = [], []
    for u in units_in_provinces(conn, all_provinces):
        if min_lon <= u.lon <= max_lon and min_lat <= u.lat <= max_lat:
            routed.append(u)
        elif u.province_id in selected_ids:
            outside_extract.append({"osm_id": u.osm_id, "name": u.name, "province": u.province,
                                    "reason": "representative point outside the routing extract bbox (A9)"})
    dists = road_distances(osrm_url, (lon, lat), [(u.lon, u.lat) for u in routed])
    info: dict[int, dict[str, Any]] = {}
    chosen, unroutable, outside_scope = [], [], {}
    for u, (km, snap_m) in zip(routed, dists, strict=True):
        info[u.osm_id] = {"name": u.name, "province": u.province, "road_km": km, "snap_m": snap_m}
        if km is None:
            if u.province_id in selected_ids:
                unroutable.append({"osm_id": u.osm_id, "name": u.name, "province": u.province,
                                   "reason": "no OSRM car route from the anchor (A9)"})
            continue
        if km > b.max_km:
            continue
        if u.province_id not in selected_ids:
            outside_scope[u.province] = outside_scope.get(u.province, 0) + 1
            continue
        chosen.append({"osm_id": u.osm_id, "name": u.name, "province": u.province, "road_km": round(km, 3),
                       "snap_m": round(snap_m, 1), "rule": f"T representative point road distance <= {b.max_km} km"})
    by_province: dict[str, int] = {}
    for c in chosen:
        by_province[c["province"]] = by_province.get(c["province"], 0) + 1
    b.note(f"total ({scope}): {len(chosen)} units; by province {by_province}; unroutable {len(unroutable)}; "
           f"outside routing extract {len(outside_extract)}")
    stats = {"anchor": {"osm_node": b.rules["total"]["anchor"]["osm_node"], "name": name, "lon": lon, "lat": lat},
             "province_scope": scope, "units_routed": len(routed), "units_by_province": by_province,
             "excluded_outside_routing_extract": outside_extract, "excluded_unroutable": unroutable,
             "units_in_range_outside_scope": outside_scope}
    return sorted(chosen, key=lambda r: r["osm_id"]), stats, info


# --- analyses (report only) ------------------------------------------------------------


def sensitivity_150(conn: Connection, info: dict[int, dict[str, Any]], chosen_ids: set[int], osrm_url: str,
                    b: Build) -> list[dict[str, Any]]:
    """A4: sample points inside units whose representative-point distance is near the
    limit, to show units that are only partly within (or beyond) the road limit."""
    band = float(b.rules["total"].get("sensitivity_band_km", 0))
    n = int(b.rules["total"].get("sensitivity_points_per_unit", 0))
    if not band or not n:
        return []
    near = [uid for uid, i in info.items() if i["road_km"] is not None and abs(i["road_km"] - b.max_km) <= band]
    samples: list[tuple[int, float, float]] = []
    for uid in near:
        pts = conn.execute(text(f"""SELECT ST_X(g), ST_Y(g) FROM (
            SELECT (ST_Dump(ST_GeneratePoints(ST_Intersection(geom, {envelope_sql(b)}), :n, 1))).geom AS g
            FROM {SCHEMA}.units WHERE osm_id = :id) s"""), {"n": n, "id": uid}).all()
        samples.extend((uid, x, y) for x, y in pts)
    lon, lat, _ = anchor_point(conn, b)
    dists = road_distances(osrm_url, (lon, lat), [(x, y) for _, x, y in samples])
    per_unit: dict[int, list[float | None]] = {}
    for (uid, _, _), (km, _) in zip(samples, dists, strict=True):
        per_unit.setdefault(uid, []).append(km)
    rows = []
    for uid, kms in sorted(per_unit.items()):
        ok = [k for k in kms if k is not None]
        within = sum(k <= b.max_km for k in ok)
        included = uid in chosen_ids
        if included and within < len(kms):
            verdict = "INCLUDED_PARTLY_BEYOND_LIMIT"
        elif not included and within > 0:
            verdict = "EXCLUDED_PARTLY_WITHIN_LIMIT"
        else:
            verdict = "CONSISTENT"
        rows.append({"osm_id": uid, "name": info[uid]["name"], "province": info[uid]["province"],
                     "included": included, "rep_point_km": round(info[uid]["road_km"], 3), "samples": len(kms),
                     "samples_within": within, "samples_unroutable": len(kms) - len(ok),
                     "sample_min_km": round(min(ok), 3) if ok else None, "sample_max_km": round(max(ok), 3) if ok else None,
                     "verdict": verdict})
    b.note(f"A4 sensitivity: {len(rows)} units within ±{band} km sampled at {n} points; "
           + ", ".join(f"{v}: {sum(r['verdict'] == v for r in rows)}" for v in
                       ("CONSISTENT", "INCLUDED_PARTLY_BEYOND_LIMIT", "EXCLUDED_PARTLY_WITHIN_LIMIT")))
    return rows


def classify_components(conn: Connection, version: str, area_type: str, unit_ids: list[int], osrm_url: str,
                        b: Build, osm_areas: list[str] | None = None) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    """A6: classify every disjoint component of a stored candidate geometry."""
    conn.execute(text(f"DROP TABLE IF EXISTS {SCHEMA}.comps"))
    conn.execute(text(f"""CREATE TABLE {SCHEMA}.comps AS
        SELECT row_number() OVER (ORDER BY ST_Area(d.geom) DESC) AS idx, d.geom AS g
        FROM (SELECT (ST_Dump(geom)).geom FROM public.service_areas
              WHERE area_type = :a AND service_area_version = :v) d"""), {"a": area_type, "v": version})
    rows = conn.execute(text(f"""SELECT c.idx, ST_Area(c.g::geography) / 1e6 AS km2,
            ST_NumInteriorRings(c.g) AS holes,
            ST_X(ST_PointOnSurface(c.g)) AS lon, ST_Y(ST_PointOnSurface(c.g)) AS lat,
            (SELECT count(*) FROM {SCHEMA}.units u WHERE u.osm_id = ANY(:ids) AND u.geom && c.g
                AND ST_Area(ST_Intersection(u.geom, c.g)) >= 0.999 * ST_Area(u.geom)) AS whole_units,
            (SELECT string_agg(DISTINCT u.name, ', ') FROM {SCHEMA}.units u
                WHERE u.osm_id = ANY(:ids) AND ST_Intersects(u.geom, ST_PointOnSurface(c.g))) AS unit_names,
            COALESCE((SELECT min(ST_Distance(c.g::geography, o.g::geography)) FROM {SCHEMA}.comps o
                WHERE o.idx <> c.idx AND ST_DWithin(c.g, o.g, 0.5)), 1e9) AS gap_m,
            EXISTS (SELECT 1 FROM {SCHEMA}.places p WHERE p.osm_type || '/' || p.osm_id = ANY(:areas)
                AND ST_Intersects(p.geom_full, ST_PointOnSurface(c.g))) AS is_osm_area
        FROM {SCHEMA}.comps c ORDER BY c.idx"""), {"ids": unit_ids, "areas": osm_areas or []}).mappings().all()
    main_holes = conn.execute(text(f"""SELECT count(*) AS n,
            count(*) FILTER (WHERE ST_Area(r.geom::geography) / 1e6 < :sliver) AS tiny
        FROM (SELECT (ST_DumpRings(g)).* FROM {SCHEMA}.comps WHERE idx = 1) r WHERE r.path[1] > 0"""),
        {"sliver": SLIVER_MAX_KM2}).mappings().one()
    out = []
    for r in rows:
        snapped = httpx.get(f"{b_osrm(osrm_url)}/nearest/v1/driving/{r['lon']:.6f},{r['lat']:.6f}",
                            headers={"Connection": "close"}, timeout=10).json()
        loc = snapped["waypoints"][0]["location"] if snapped.get("code") == "Ok" else None
        road_inside = bool(loc) and conn.execute(text(
            f"SELECT ST_DWithin(g::geography, ST_SetSRID(ST_MakePoint(:x, :y), 4326)::geography, 1) FROM {SCHEMA}.comps WHERE idx = :i"),
            {"x": loc[0], "y": loc[1], "i": r["idx"]}).scalar_one()
        if r["idx"] == 1:
            category = "MAIN_BODY"
        elif r["whole_units"] > 0:
            category = "SEPARATED_WHOLE_UNIT (valid administrative geometry)"
        elif r["is_osm_area"]:
            category = "U3_URBAN_DEVELOPMENT_POLYGON (not contiguous with the main body)"
        elif r["km2"] < SLIVER_MAX_KM2 and r["gap_m"] < SLIVER_MAX_GAP_M:
            category = "SLIVER_SUSPECTED (overlay / data artefact)"
        else:
            category = "UNIT_PART_SEPARATED (island / exclave of a unit)"
        if not road_inside and r["idx"] != 1:
            category += " + NO_ROUTABLE_ROAD_INSIDE"
        out.append({"area_type": area_type, "component": r["idx"], "km2": round(r["km2"], 6), "holes": r["holes"],
                    "whole_units": r["whole_units"], "units_at_point": r["unit_names"],
                    "gap_to_nearest_component_m": None if r["gap_m"] >= 1e9 else round(r["gap_m"], 1),
                    "road_inside": road_inside, "category": category})
    summary: dict[str, Any] = {"components": len(out), "main_body_holes": main_holes["n"],
                               "main_body_tiny_holes_suspected_gaps": main_holes["tiny"]}
    for c in out:
        key = c["category"]
        summary[key] = summary.get(key, 0) + 1
    b.note(f"A6 {area_type}: {summary}")
    return out, summary


def b_osrm(url: str) -> str:
    return url.rstrip("/")


def routing_coverage(conn: Connection, total_ids: list[int], b: Build) -> list[dict[str, Any]]:
    """A9: included units whose polygon extends beyond the routing extract."""
    rows = conn.execute(text(f"""SELECT osm_id, name,
            ST_Area(ST_Difference(geom, {envelope_sql(b)})::geography) / 1e6 AS outside_km2,
            ST_Area(geom::geography) / 1e6 AS km2
        FROM {SCHEMA}.units WHERE osm_id = ANY(:ids)
          AND NOT ST_CoveredBy(geom, {envelope_sql(b)})"""), {"ids": total_ids}).mappings().all()
    return [{"osm_id": r["osm_id"], "name": r["name"], "outside_bbox_km2": round(r["outside_km2"], 4),
             "unit_km2": round(r["km2"], 3)} for r in rows]


def resolve_admin_mapping(conn: Connection, city: Any, urban_ids: set[int], b: Build) -> list[dict[str, Any]]:
    out = []
    for m in b.rules.get("admin_mapping", []):
        names = re.findall(r"(?:Phường|Xã) [^+/(]+?(?=\s*(?:\(|\+|/|$))", m["unit"])
        resolved = []
        for name in names:
            rows = conn.execute(text(f"""SELECT u.osm_id FROM {SCHEMA}.units u, {SCHEMA}.units c
                WHERE c.osm_id = :city AND u.admin_level = 6 AND u.name = :n
                  AND ST_Intersects(c.geom, ST_PointOnSurface(u.geom))"""), {"city": city.osm_id, "n": name.strip()}).scalars().all()
            scope = "city"
            if not rows:  # e.g. Phường Phố Hiến lies in Hưng Yên, not in the city
                rows = conn.execute(text(f"SELECT osm_id FROM {SCHEMA}.units WHERE admin_level = 6 AND name = :n"),
                                    {"n": name.strip()}).scalars().all()
                scope = "any province (name may be ambiguous)" if len(rows) > 1 else "outside the city"
            resolved.append({"name": name.strip(), "osm_relations": list(rows), "search_scope": scope,
                             "in_urban_selection": any(r in urban_ids for r in rows)})
        out.append(m | {"resolved_units": resolved})
    return out


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


# --- geometry, persistence -----------------------------------------------------------


def geometry_sql(kind: str) -> str:
    """kind 'units': union of admin units; 'urban': units + U3 areas clipped to the city."""
    units = f"SELECT geom AS g FROM {SCHEMA}.units WHERE osm_id = ANY(:ids)"
    if kind == "urban":
        units += (f" UNION ALL SELECT ST_CollectionExtract(ST_Intersection(p.geom_full, c.geom), 3) FROM {SCHEMA}.places p, "
                  f"{SCHEMA}.units c WHERE c.osm_id = :city AND p.osm_type || '/' || p.osm_id = ANY(:areas)")
    return f"SELECT ST_Multi(ST_CollectionExtract(ST_MakeValid(ST_Union(g)), 3)) FROM ({units}) s"


def compute_version(b: Build, urban_ids: list[int], urban_areas: list[str], total_ids: list[int], anchor_id: int) -> str:
    material = {
        "manifest": b.manifest,  # source/routing extract MD5s, export MD5s, bbox
        "rules": b.rules,
        "max_total_service_radius_km": b.max_km,
        "anchor": anchor_id,
        "urban_unit_ids": urban_ids,
        "urban_osm_areas": urban_areas,
        "total_unit_ids": total_ids,
    }
    digest = hashlib.sha256(json.dumps(material, sort_keys=True, ensure_ascii=False).encode()).hexdigest()
    return f"sa-cand-{digest[:12]}"


def persist(conn: Connection, version: str, area_type: str, geom_sql: str, params: dict[str, Any],
            source: dict[str, Any]) -> str:
    inserted = conn.execute(text(f"""INSERT INTO public.service_areas (area_type, service_area_version, status, geom, source_json)
        SELECT :area_type, :version, 'CANDIDATE', ({geom_sql}), CAST(:source AS jsonb)
        ON CONFLICT (area_type, service_area_version) DO NOTHING"""),
        params | {"area_type": area_type, "version": version, "source": json.dumps(source, ensure_ascii=False)}).rowcount
    if inserted:
        return "inserted"
    same = conn.execute(text(f"""SELECT ST_Equals(geom, ({geom_sql})) FROM public.service_areas
        WHERE area_type = :area_type AND service_area_version = :version"""),
        params | {"area_type": area_type, "version": version}).scalar_one()
    if not same:
        raise SystemExit(f"{area_type} {version} already stored with a different geometry - import is not stable")
    return "unchanged (ST_Equals)"


def geometry_checks(conn: Connection, version: str) -> dict[str, Any]:
    row = conn.execute(text("""WITH u AS (SELECT geom FROM service_areas WHERE area_type='URBAN' AND service_area_version=:v),
                                    t AS (SELECT geom FROM service_areas WHERE area_type='TOTAL' AND service_area_version=:v)
        SELECT ST_IsValid((SELECT geom FROM u)) AS urban_valid, ST_IsValid((SELECT geom FROM t)) AS total_valid,
               ST_NumGeometries((SELECT geom FROM u)) AS urban_parts, ST_NumGeometries((SELECT geom FROM t)) AS total_parts,
               ST_Area((SELECT geom FROM u)::geography) / 1e6 AS urban_km2, ST_Area((SELECT geom FROM t)::geography) / 1e6 AS total_km2,
               ST_CoveredBy((SELECT geom FROM u), (SELECT geom FROM t)) AS urban_within_total"""), {"v": version}).mappings().one()
    return {k: (round(v, 4) if isinstance(v, float) else v) for k, v in row.items()}


# --- outputs ------------------------------------------------------------------------------


def write_csv(path: Path, rows: list[dict[str, Any]]) -> None:
    if not rows:
        path.write_text("", encoding="utf-8")
        return
    fieldnames: list[str] = []
    for r in rows:  # union of keys, first-seen order (rows may carry optional fields)
        fieldnames.extend(k for k in r if k not in fieldnames)
    with path.open("w", newline="", encoding="utf-8") as fh:
        w = csv.DictWriter(fh, fieldnames=fieldnames)
        w.writeheader()
        for r in rows:
            w.writerow({k: (json.dumps(v, ensure_ascii=False) if isinstance(v, list | dict) else v) for k, v in r.items()})


def write_bundle(conn: Connection, out: Path, version: str, report: dict[str, Any]) -> None:
    out.mkdir(parents=True, exist_ok=True)
    for area_type, name in (("URBAN", "urban"), ("TOTAL", "total")):
        geom = conn.execute(text("""SELECT ST_AsGeoJSON(geom, 6) FROM public.service_areas
            WHERE area_type = :a AND service_area_version = :v"""), {"a": area_type, "v": version}).scalar_one()
        fc = {"type": "FeatureCollection", "features": [{"type": "Feature", "geometry": json.loads(geom), "properties": {
            "area_type": area_type, "service_area_version": version, "status": "CANDIDATE",
            "approval": "PENDING_OWNER_APPROVAL"}}]}
        (out / f"{name}.geojson").write_text(json.dumps(fc, ensure_ascii=False), encoding="utf-8")
    units = ([{"area_type": "URBAN", **u} for u in report["urban_units"]]
             + [{"area_type": "URBAN_OSM_AREA", "osm_id": a["osm"], "name": a["osm_name"], "province": "",
                 "rule": a["rule"]} for a in report["urban_areas"]]
             + [{"area_type": "TOTAL", **t} for t in report["total_units"]])
    write_csv(out / "units.csv", [{k: u.get(k, "") for k in ("area_type", "osm_id", "name", "province", "rule", "road_km", "snap_m")}
                                  for u in units])
    write_csv(out / "excluded_units.csv", report["total_stats"]["excluded_outside_routing_extract"]
              + report["total_stats"]["excluded_unroutable"])
    write_csv(out / "admin_mapping.csv", report["admin_mapping"])
    write_csv(out / "components.csv", report["components"])
    write_csv(out / "sensitivity_150km.csv", report["sensitivity"])
    write_csv(out / "routing_coverage.csv", report["routing_coverage"])
    (out / "report.json").write_text(json.dumps(report, ensure_ascii=False, indent=2, default=str), encoding="utf-8")
    (out / "REVIEW.md").write_text(render_review(report), encoding="utf-8")
    sums = []
    for f in sorted(out.iterdir()):
        if f.name != "CHECKSUMS.sha256" and f.is_file() and f.name != "REVIEW.md":
            sums.append(f"{hashlib.sha256(f.read_bytes()).hexdigest()}  {f.name}")
    (out / "CHECKSUMS.sha256").write_text("\n".join(sums) + "\n", encoding="utf-8")


def _table(headers: list[str], rows: list[list[Any]]) -> list[str]:
    return ["| " + " | ".join(headers) + " |", "|" + "---|" * len(headers),
            *["| " + " | ".join("" if v is None else str(v) for v in r) + " |" for r in rows]]


def render_review(r: dict[str, Any]) -> str:
    c, ts = r["checks"], r["total_stats"]
    comp_summary = r["component_summary"]
    lines = [
        f"# Service-area candidate `{r['service_area_version']}` — review bundle",
        "",
        "**Status: CANDIDATE — PENDING_OWNER_APPROVAL. Not GEOMETRY_APPROVED.**",
        f"Rules: `{r['rules_file']}` (`{r['rules']['rules_id']}`). Generated by `app.modules.trip.service_area_build`; "
        "do not edit by hand. File checksums: `CHECKSUMS.sha256`.",
        "",
        "## 1. Administrative mapping (A1/A3)",
        "",
        *_table(["Revision 9 name", "Current unit(s)", "QĐ19 code(s)", "NQ1656", "Confidence", "OSM relation(s)", "In urban", "Note"],
                [[m["r9_name"], m["unit"], m.get("qd19_code"), m.get("nq1656"), m["confidence"],
                  "; ".join(f"{u['name']}: {', '.join(f'r{i}' for i in u['osm_relations']) or 'NOT FOUND'}" for u in m["resolved_units"]),
                  "; ".join(f"{u['name']}={u['in_urban_selection']}" for u in m["resolved_units"]), m.get("note", "")]
                 for m in r["admin_mapping"]]),
        "",
        "## 2. Selected areas",
        f"- Urban: {len(r['urban_units'])} units (" + ", ".join(f"{k}: {v}" for k, v in r["urban_by_rule"].items())
        + f") + {len(r['urban_areas'])} OSM urban-development polygons (U3).",
        f"- Total ({ts['province_scope']}): {len(r['total_units'])} units; by province: {ts['units_by_province']}.",
        "",
        "U3 polygons:",
        "",
        *_table(["OSM", "Label", "OSM name", "km² in city", "Lies in unit", "Note"],
                [[a["osm"], a["label"], a["osm_name"], a["km2_in_city"], a["containing_unit"], a.get("note") or ""]
                 for a in r["urban_areas"]]),
        "",
        "Section 1 neighbour names → current provinces (documentation; scope is not limited to them):",
        "",
        *_table(["Revision 9 name(s)", "Current OSM unit", "ISO", "Evidence"],
                [[", ".join(p["neighbours"]), f"{p['name']} (r{p['osm_id']})", p["iso"] or "", p["evidence"]] for p in r["provinces"]]),
        "",
        "## 3. Source and traceability",
        *[f"- {k}: `{v}`" for k, v in r["manifest"].items()],
        f"- anchor: node/{ts['anchor']['osm_node']} '{ts['anchor']['name']}' ({ts['anchor']['lon']:.7f}, {ts['anchor']['lat']:.7f})",
        f"- max_total_service_radius_km (baseline): {r['max_km']}",
        "",
        "## 4. Rules",
        "- Units: OSM `boundary=administrative` relations from the unclipped Geofabrik source; `ST_MakeValid`, polygons only.",
        "- Unit ↔ province by `ST_PointOnSurface`.",
        "- **Urban**: U1 every `Phường …` of the city; U2 named communes; U3 listed OSM urban-development polygons (clipped to the city).",
        f"- **Total**: units (scope `{ts['province_scope']}`) whose `ST_PointOnSurface` is within {r['max_km']} km OSRM car road distance "
        "from the anchor; units whose point is outside the routing bbox or unroutable are excluded (A9).",
        "",
        "## 5. Topology checks (A6)",
        "",
        *_table(["Check", "Value"], [[k, v] for k, v in c.items()]),
        "",
        "Component classification (no geometry was modified):",
        "",
        *_table(["Area", "Category", "Count"],
                [[area, k, v] for area, s in comp_summary.items() for k, v in s.items() if k not in ("components",)]),
        "",
        "Non-main components are listed in `components.csv`.",
        "",
        "## 6. 150 km limit sensitivity (A4)",
        f"Units within ±{r['rules']['total'].get('sensitivity_band_km')} km of the limit, sampled at "
        f"{r['rules']['total'].get('sensitivity_points_per_unit')} deterministic points each (`ST_GeneratePoints`, seed 1). "
        "**Checking only the representative point does not prove every point of a unit is within 150 km.**",
        "",
        *_table(["Verdict", "Units"], [[v, sum(x["verdict"] == v for x in r["sensitivity"])] for v in
                                        ("CONSISTENT", "INCLUDED_PARTLY_BEYOND_LIMIT", "EXCLUDED_PARTLY_WITHIN_LIMIT")]),
        "",
        "Details: `sensitivity_150km.csv`.",
        "",
        "## 7. Routing coverage (A9)",
        f"- Excluded, representative point outside the routing bbox: {len(ts['excluded_outside_routing_extract'])}",
        f"- Excluded, no OSRM route: {len(ts['excluded_unroutable'])}",
        f"- Included units whose polygon extends beyond the routing bbox: {len(r['routing_coverage'])} "
        f"({round(sum(x['outside_bbox_km2'] for x in r['routing_coverage']), 3)} km² outside) — `routing_coverage.csv`",
        "- Full list of exclusions with reasons: `excluded_units.csv`.",
        "",
        "## 8. Boundary locations",
        "",
        *_table(["Location", "OSM", "Expected urban", "Actual urban", "In total", "Unit / province", "Result"],
                [[t["label"], t.get("osm") or "—", t.get("expected_urban"), t.get("in_urban", "—"), t.get("in_total", "—"),
                  f"{t.get('unit', '—')} / {t.get('province', '—')}", f"**{t['result']}** {t.get('detail', '')}"]
                 for t in r["locations"]]),
        "",
        "## 9. Version",
        "`sa-cand-` + first 12 hex of SHA-256 over the export MANIFEST, the parsed rules, max_total_service_radius_km, "
        "anchor, and the selected unit ids / OSM areas.",
        f"- This run: `{r['service_area_version']}`; persistence: {r['persist']}",
        "",
        "## 10. Open conflicts / insufficient data",
        *([f"- {x}" for x in r["conflicts"]] or ["- none detected by the pipeline"]),
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
    manifest = read_manifest(args.sources / "MANIFEST")
    bbox = tuple(float(x) for x in manifest["bbox"].split(","))
    b = Build(manifest=manifest, rules=rules, bbox=bbox,  # type: ignore[arg-type]
              max_km=float(get_config_baseline()["spatial_and_service_areas"]["max_total_service_radius_km"]))

    engine = create_engine(settings.database_url)
    with engine.begin() as conn:
        load_inputs(conn, args.sources, b)
        city = select_city(conn, b)
        urban, urban_areas = select_urban(conn, city, b)
        provinces = map_neighbours(conn, city, b)
        total, total_stats, info = select_total(conn, provinces, settings.osrm_car_url, b)
        urban_ids = [u["osm_id"] for u in urban]
        area_keys = [a["osm"] for a in urban_areas]
        total_ids = [t["osm_id"] for t in total]
        missing = sorted(set(urban_ids) - set(total_ids))
        if missing:
            b.conflicts.append(f"{len(missing)} urban units are not in the total area (road distance rule): {missing}")
        version = compute_version(b, urban_ids, area_keys, total_ids, rules["total"]["anchor"]["osm_node"])
        source = {"manifest": b.manifest, "rules_id": rules["rules_id"], "rules_status": rules["status"]}
        persist_result = {
            "URBAN": persist(conn, version, "URBAN", geometry_sql("urban"),
                             {"ids": urban_ids, "areas": area_keys, "city": city.osm_id}, source),
            "TOTAL": persist(conn, version, "TOTAL", geometry_sql("units"), {"ids": total_ids}, source),
        }
        checks = geometry_checks(conn, version)
        if not checks["urban_within_total"]:
            b.conflicts.append("urban area is not fully covered by the total area")
        components, summaries = [], {}
        for area_type, ids, areas in (("URBAN", urban_ids, area_keys), ("TOTAL", total_ids, [])):
            comps, summary = classify_components(conn, version, area_type, ids, settings.osrm_car_url, b, areas)
            components.extend(c for c in comps if c["component"] != 1)
            summaries[area_type] = summary
            if summary["components"] > 1:
                b.conflicts.append(f"{area_type.lower()} area has {summary['components']} disjoint components "
                                   "(classified in components.csv; nothing removed)")
        sensitivity = sensitivity_150(conn, info, set(total_ids), settings.osrm_car_url, b)
        partial = [s for s in sensitivity if s["verdict"] != "CONSISTENT"]
        if partial:
            b.conflicts.append(f"{len(partial)} units near the 150 km limit are only partly on the selected side (A4)")
        coverage = routing_coverage(conn, total_ids, b)
        mapping = resolve_admin_mapping(conn, city, set(urban_ids), b)
        for m in mapping:
            if m["confidence"] in ("PENDING", "LOW"):
                b.conflicts.append(f"admin mapping '{m['r9_name']}': confidence {m['confidence']} - {m.get('note', '')}")
            for u in m["resolved_units"]:
                if not u["osm_relations"]:
                    b.conflicts.append(f"admin mapping '{m['r9_name']}': unit '{u['name']}' not found in OSM")
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
            "provinces": provinces, "urban_units": urban, "urban_areas": urban_areas, "urban_by_rule": by_rule,
            "total_units": total, "total_stats": total_stats, "checks": checks, "component_summary": summaries,
            "components": components, "sensitivity": sensitivity, "routing_coverage": coverage,
            "admin_mapping": mapping, "locations": locations, "persist": persist_result,
            "conflicts": b.conflicts, "log": b.log,
        }
        write_bundle(conn, args.out / version, version, report)
        conn.execute(text(f"DROP SCHEMA {SCHEMA} CASCADE"))
    b.note(f"service_area_version={version} persist={persist_result} -> {args.out / version}")


if __name__ == "__main__":
    main()
