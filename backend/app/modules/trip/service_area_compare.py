"""Compare two service_areas versions (owner decision "P1: GEOGRAPHY & S1 CLOSURE" §B):
area, disjoint components, symmetric differences, unit changes, test-location
changes, membership changes of every OSM place node inside the routing bbox,
and the effect on the geographic edge-case evaluation. Read-only.

Run (compose): docker compose --profile service-area run --rm service-area-build \
    python -m app.modules.trip.service_area_compare --old <version> --new <version>
"""

import argparse
import json
from collections import Counter
from pathlib import Path
from typing import Any

from sqlalchemy import create_engine, text

from app.core.settings import get_settings

PLACE_KINDS = ("city", "town", "suburb", "quarter", "neighbourhood", "village", "hamlet", "isolated_dwelling")


def load_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8")) if path.exists() else None


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--old", required=True)
    parser.add_argument("--new", required=True)
    parser.add_argument("--places", type=Path, default=Path("/osm/service_area/places.geojsonseq"))
    parser.add_argument("--out", type=Path, default=Path("/out"))
    args = parser.parse_args()

    engine = create_engine(get_settings().database_url)
    old_r = load_json(args.out / args.old / "report.json")
    new_r = load_json(args.out / args.new / "report.json")
    lines = [f"# Service-area comparison `{args.old}` → `{args.new}`", "",
             "Both versions are CANDIDATE (not approved). Read-only comparison; no geometry was changed.", ""]

    with engine.connect() as conn:
        geo = conn.execute(text("""
            WITH o AS (SELECT area_type, geom FROM service_areas WHERE service_area_version = :o),
                 n AS (SELECT area_type, geom FROM service_areas WHERE service_area_version = :n)
            SELECT o.area_type,
                   ST_Area(o.geom::geography) / 1e6 AS old_km2, ST_Area(n.geom::geography) / 1e6 AS new_km2,
                   ST_NumGeometries(o.geom) AS old_parts, ST_NumGeometries(n.geom) AS new_parts,
                   ST_Area(ST_Difference(n.geom, o.geom)::geography) / 1e6 AS added_km2,
                   ST_Area(ST_Difference(o.geom, n.geom)::geography) / 1e6 AS removed_km2
            FROM o JOIN n USING (area_type) ORDER BY o.area_type DESC"""), {"o": args.old, "n": args.new}).mappings().all()
        lines += ["## 1. Area and components", "",
                  "| Area | Old km² | New km² | Added km² | Removed km² | Old parts | New parts |", "|---|---|---|---|---|---|---|",
                  *[f"| {g['area_type']} | {g['old_km2']:.3f} | {g['new_km2']:.3f} | {g['added_km2']:.3f} | {g['removed_km2']:.3f} | "
                    f"{g['old_parts']} | {g['new_parts']} |" for g in geo], ""]

        # Membership changes of OSM place nodes inside the routing bbox.
        bbox = [float(x) for x in conn.execute(text(
            "SELECT source_json->'manifest'->>'bbox' FROM service_areas WHERE service_area_version = :n LIMIT 1"),
            {"n": args.new}).scalar_one().split(",")]
        pts = []
        with args.places.open(encoding="utf-8") as fh:
            for line in fh:
                line = line.strip().lstrip("\x1e")
                if not line:
                    continue
                f = json.loads(line)
                p = f["properties"]
                if p.get("@type") != "node" or p.get("place") not in PLACE_KINDS:
                    continue
                x, y = f["geometry"]["coordinates"]
                if bbox[0] <= x <= bbox[2] and bbox[1] <= y <= bbox[3]:
                    pts.append({"id": p["@id"], "name": p.get("name") or "", "x": x, "y": y})
        conn.execute(text("CREATE TEMP TABLE cmp_pts (id bigint, name text, geom geometry(Point, 4326))"))
        conn.execute(text("INSERT INTO cmp_pts VALUES (:id, :name, ST_SetSRID(ST_MakePoint(:x, :y), 4326))"), pts)
        conn.execute(text("CREATE INDEX ON cmp_pts USING gist (geom)"))
        changes = conn.execute(text("""
            SELECT a.area_type, p.id, p.name,
                   ST_Intersects(o.geom, p.geom) AS in_old, ST_Intersects(n.geom, p.geom) AS in_new
            FROM cmp_pts p
            CROSS JOIN (VALUES ('URBAN'), ('TOTAL')) a(area_type)
            JOIN service_areas o ON o.area_type = a.area_type AND o.service_area_version = :o
            JOIN service_areas n ON n.area_type = a.area_type AND n.service_area_version = :n
            WHERE ST_Intersects(o.geom, p.geom) <> ST_Intersects(n.geom, p.geom)"""),
            {"o": args.old, "n": args.new}).mappings().all()
        counts = Counter((c["area_type"], "entered" if c["in_new"] else "left") for c in changes)
        lines += ["## 2. Points that change status", "",
                  f"Sample: every OSM `place=*` node ({', '.join(PLACE_KINDS)}) inside the routing bbox — {len(pts)} points.", "",
                  "| Area | Entered (out → in) | Left (in → out) |", "|---|---|---|",
                  *[f"| {a} | {counts[(a, 'entered')]} | {counts[(a, 'left')]} |" for a in ("URBAN", "TOTAL")], "",
                  "Urban status changes (named points):", ""]
        urban_changes = [c for c in changes if c["area_type"] == "URBAN" and c["name"]]
        lines += [f"- node/{c['id']} {c['name']}: {'outside → URBAN' if c['in_new'] else 'URBAN → outside'}"
                  for c in sorted(urban_changes, key=lambda c: c["name"])[:40]]
        if len(urban_changes) > 40:
            lines.append(f"- … {len(urban_changes) - 40} more")
        lines.append("")

    if old_r and new_r:
        def units(r: dict[str, Any], key: str) -> dict[int, dict[str, Any]]:
            return {u["osm_id"]: u for u in r[key]}

        ou, nu = units(old_r, "urban_units"), units(new_r, "urban_units")
        ot, nt = units(old_r, "total_units"), units(new_r, "total_units")
        added_t = Counter(nt[i]["province"] for i in set(nt) - set(ot))
        removed_t = Counter(ot[i]["province"] for i in set(ot) - set(nt))
        lines += ["## 3. Unit changes", "",
                  "Urban units added: " + (", ".join(nu[i]["name"] for i in sorted(set(nu) - set(ou))) or "none"),
                  "",
                  "Urban units removed: " + (", ".join(ou[i]["name"] for i in sorted(set(ou) - set(nu))) or "none"),
                  "",
                  "Urban OSM areas (U3) added: " + (", ".join(a["osm"] + " " + (a["label"] or "")
                                                               for a in new_r.get("urban_areas", [])) or "none"),
                  "",
                  f"Total units added by province: {dict(added_t) or 'none'}",
                  "",
                  f"Total units removed by province: {dict(removed_t) or 'none'}", ""]
        old_loc = {loc.get("osm"): loc for loc in old_r["locations"]}
        lines += ["## 4. Test locations", "", "| Location | Old urban / result | New urban / result |", "|---|---|---|"]
        for loc in new_r["locations"]:
            o = old_loc.get(loc.get("osm"))
            old_txt = f"{o.get('in_urban')} / {o['result']}" if o else "not tested in old version"
            lines.append(f"| {loc['label']} | {old_txt} | {loc.get('in_urban')} / {loc['result']} |")
        lines.append("")

    old_e = (load_json(args.out / args.old / "trip_classification_reeval_p1_closure.json")
             or load_json(args.out / args.old / "trip_classification_eval.json"))
    new_e = load_json(args.out / args.new / "trip_classification_eval.json")
    if isinstance(old_e, dict) and isinstance(new_e, dict):
        old_cases = {c["case"]: c for c in old_e["cases"]}
        lines += ["## 5. Effect on Trip Intent classification (same deterministic cases)", "",
                  "| Case | Old actual (branch) / result | New actual (branch) / result |", "|---|---|---|"]
        for c in new_e["cases"]:
            o = old_cases.get(c["case"])
            old_txt = f"{o['actual']} ({o['branch']}) / {o['result_on_candidate']}" if o else "—"
            lines.append(f"| {c['case']} | {old_txt} | {c['actual']} ({c['branch']}) / {c['result_on_candidate']} |")
        lines.append("")

    path = args.out / f"COMPARE_{args.old}_vs_{args.new}.md"
    path.write_text("\n".join(lines), encoding="utf-8")
    print("\n".join(lines))


if __name__ == "__main__":
    main()
