"""Owner approval gate for a service-area version (owner decision "P1 OWNER APPROVAL
& FINAL CLOSURE GATES", section 2).

The owner approved sa-cand-0d5347b4294e CONDITIONALLY. This command checks every
condition and only then marks the version APPROVED (reference
GEOMETRY_APPROVED_FOR_MVP). If any check fails nothing is changed, the version stays
CANDIDATE and the failures are reported.

  G1 version rows + full checksums: every file of CHECKSUMS.sha256 re-hashed; the
     stored geometry of URBAN / TOTAL / EXCLUDED equals the bundle GeoJSON
  G2 evidence of the candidate: report.json, U4 Đông Anh polygon, historic-source concordance
  G3 a FRESH evaluation (written under a new report name) - every case PASS
  G4 Đông Anh -> Hoàn Kiếm = URBAN
  G5 Phenikaa -> La Phù = URBAN through the 15 km buffer (branch 2b)
  G6 points beyond 150 km rejected (tier 2, BEYOND_MAX_ROAD_DISTANCE)
  G7 outside-area / bad-snap / EXCLUDED points rejected; no ferry step with the policy
  G8 re-import gives the same GeoJSON hashes; existing evidence is never overwritten

Run (compose): docker compose --profile service-area run --rm service-area-build \
    python -m app.modules.trip.service_area_approve --version <v> --eval-report <name> \
    --reimport-dir /tmp/repro/<v> --reference "<text>"
"""

import argparse
import hashlib
import json
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from sqlalchemy import create_engine, text

from app.core.settings import get_settings
from app.modules.trip.service_area_build import ensure_new_bundle

LAYERS = (("URBAN", "urban.geojson"), ("TOTAL", "total.geojson"), ("EXCLUDED", "excluded.geojson"))
MVP_LABEL = "GEOMETRY_APPROVED_FOR_MVP"


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def gate(name: str, ok: bool, detail: Any) -> dict[str, Any]:
    return {"gate": name, "result": "PASS" if ok else "FAIL", "detail": detail}


def case(cases: list[dict[str, Any]], prefix: str) -> dict[str, Any] | None:
    return next((c for c in cases if c["case"].startswith(prefix)), None)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--version", required=True)
    parser.add_argument("--eval-report", required=True, help="report name of a fresh boundary_eval run")
    parser.add_argument("--reimport-dir", type=Path, required=True)
    parser.add_argument("--reference", required=True)
    parser.add_argument("--out", type=Path, default=Path("/out"))
    args = parser.parse_args()
    bundle = args.out / args.version
    gates: list[dict[str, Any]] = []
    engine = create_engine(get_settings().database_url)

    with engine.begin() as conn:
        rows = {t: (st, gj) for t, st, gj in conn.execute(text(
            "SELECT area_type, status, ST_AsGeoJSON(geom, 6) FROM service_areas WHERE service_area_version = :v"),
            {"v": args.version}).all()}
        # G1
        listed = [line.split("  ", 1) for line in (bundle / "CHECKSUMS.sha256").read_text(encoding="utf-8").splitlines() if line]
        bad = [f for h, f in listed if sha256(bundle / f) != h]
        geom_mismatch = []
        for layer, fname in LAYERS:
            fc = json.loads((bundle / fname).read_text(encoding="utf-8"))
            feat = fc["features"][0]
            if layer not in rows or json.loads(rows[layer][1]) != feat["geometry"] \
                    or feat["properties"]["service_area_version"] != args.version:
                geom_mismatch.append(layer)
        gates.append(gate("G1 version rows, checksums, stored geometry = bundle",
                          set(rows) == {"URBAN", "TOTAL", "EXCLUDED"} and not bad and not geom_mismatch
                          and all(st == "CANDIDATE" for st, _ in rows.values()),
                          {"rows": {t: st for t, (st, _) in rows.items()}, "files_checked": len(listed),
                           "checksum_mismatch": bad, "geometry_mismatch": geom_mismatch,
                           "sha256": {f: sha256(bundle / f) for _, f in LAYERS}}))
        # G2
        report = json.loads((bundle / "report.json").read_text(encoding="utf-8"))
        hist = json.loads((bundle / "historic_sources_dong_anh.json").read_text(encoding="utf-8"))
        u4 = next((a for a in report.get("urban_historic_areas", []) if a["osm"] == "relation/17627914"), None)
        union = next((p for p in hist["osm_members_polygonized"]["polygons"] if p["polygon"] == "union of faces"), {})
        gates.append(gate("G2 candidate evidence (U4 Đông Anh, concordance)",
                          report["service_area_version"] == args.version and u4 is not None
                          and union.get("iou_with_gadm", 0) >= 0.8 and union.get("contains_osm_town_node") is True
                          and len(union.get("split_km2", {})) == 3,
                          {"u4": u4, "union_vs_gadm": union}))
        # G3 - G7 from the fresh evaluation
        ev = json.loads((bundle / f"{args.eval_report.lower()}.json").read_text(encoding="utf-8"))
        cases = ev["cases"]
        gates.append(gate("G3 fresh evaluation: every case PASS", all(c["result_on_candidate"] == "PASS" for c in cases),
                          {"report": args.eval_report, "cases": len(cases),
                           "failed": [c["case"] for c in cases if c["result_on_candidate"] != "PASS"]}))
        da, lp = case(cases, "Đông Anh (town node)"), case(cases, "Phenikaa → La Phù")
        gates.append(gate("G4 Đông Anh -> Hoàn Kiếm = URBAN", bool(da) and da["actual"] == "URBAN",
                          da and {k: da[k] for k in ("actual", "branch", "direct_distance_km")}))
        gates.append(gate("G5 Phenikaa -> La Phù = URBAN via buffer (2b)",
                          bool(lp) and lp["actual"] == "URBAN" and lp["branch"] == "2b",
                          lp and {k: lp[k] for k in ("actual", "branch", "direct_distance_km")}))
        beyond = [c for c in (case(cases, "limit > 150 km"), case(cases, "inside polygon, BEYOND")) if c]
        gates.append(gate("G6 points beyond 150 km rejected",
                          len(beyond) == 2 and all(c["actual"] == "OUT_OF_SERVICE_AREA"
                                                   and c["dropoff_tier"]["reason"] == "BEYOND_MAX_ROAD_DISTANCE" for c in beyond),
                          [{"case": c["case"], "anchor_road_km": c["dropoff_tier"]["anchor_road_km"]} for c in beyond]))
        snap, excl = case(cases, "inside polygon, NO_ROAD_ACCESS"), case(cases, "point in largest EXCLUDED")
        ferry = (ev.get("tier2_sample") or {}).get("ferry_check", {})
        cat_ba = next((r for r in ferry.get("rows", []) if r["destination"].startswith("Cát Bà")), None)
        gates.append(gate("G7 outside area / bad snap / EXCLUDED / ferry blocked",
                          bool(snap and excl and cat_ba) and snap["dropoff_tier"]["reason"] == "NO_ROAD_ACCESS"
                          and excl["dropoff_tier"]["reason"] == "UNSERVICEABLE_COMPONENT"
                          and ferry.get("ferry_steps_with_policy") == 0 and cat_ba["with_policy"]["code"] == "NoRoute",
                          {"no_road_access_snap_m": snap and snap["dropoff_tier"]["snap_m"],
                           "excluded_reason": excl and excl["dropoff_tier"]["reason"],
                           "ferry": {k: v for k, v in ferry.items() if k != "rows"},
                           "cat_ba_with_policy": cat_ba and cat_ba["with_policy"]}))
        # G8
        reimport = {f: sha256(args.reimport_dir / f) for _, f in LAYERS if (args.reimport_dir / f).exists()}
        try:
            ensure_new_bundle(bundle)
            guard = False
        except SystemExit:
            guard = True
        gates.append(gate("G8 re-import identical, evidence never overwritten",
                          reimport == {f: sha256(bundle / f) for _, f in LAYERS} and guard,
                          {"reimport_sha256": reimport, "existing_bundle_refused": guard}))

        approved = all(g["result"] == "PASS" for g in gates)
        stamp = datetime.now(UTC).isoformat(timespec="seconds")
        reference = f"{MVP_LABEL} | {args.reference}"
        if approved:
            n = conn.execute(text("""UPDATE service_areas SET status = 'APPROVED', approved_at = now(), approval_reference = :r
                WHERE service_area_version = :v AND status = 'CANDIDATE'"""), {"r": reference, "v": args.version}).rowcount
            if n != 3:
                raise SystemExit(f"expected to approve 3 rows, updated {n} - rolled back")
        result = {"service_area_version": args.version, "checked_at": stamp,
                  "outcome": MVP_LABEL if approved else "CANDIDATE (gates failed - nothing changed)",
                  "approval_reference": reference if approved else None, "gates": gates}
        name = "APPROVAL_GATES.json" if approved else f"APPROVAL_GATES_FAILED_{stamp.replace(':', '')}.json"
        if (bundle / name).exists():
            raise SystemExit(f"{bundle / name} exists - refusing to overwrite evidence (rolled back)")
        (bundle / name).write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps({k: v for k, v in result.items() if k != "gates"}, ensure_ascii=False, indent=2))
    for g in gates:
        print(f"{g['result']}  {g['gate']}")


if __name__ == "__main__":
    main()
