"""Generate the S1 scenario table (survey decision "full scenario table") from
survey/s1/questionnaire.draft.yaml - the same file the API builds designs from.

Fields: scenario_id, attributes, options, displayed_values, source, derivation,
experimental_status, approval_status. Writes survey/s1/scenario_table.csv and
docs/implementation/survey/SURVEY_S1_SCENARIO_TABLE.md.

Usage (repo root): python -I scripts/survey/scenario_table.py
"""

import csv
import sys
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[2]
Q = ROOT / "survey" / "s1" / "questionnaire.draft.yaml"
CSV_OUT = ROOT / "survey" / "s1" / "scenario_table.csv"
MD_OUT = ROOT / "docs" / "implementation" / "survey" / "SURVEY_S1_SCENARIO_TABLE.md"
FIELDS = ["scenario_id", "attributes", "options", "displayed_values", "source", "derivation",
          "experimental_status", "approval_status"]


def meta(spec: dict, **row: str) -> dict:
    return row | {k: spec.get(k, "") for k in ("source", "derivation", "experimental_status", "approval_status")}


def fmt(v: object) -> str:
    if isinstance(v, list):
        return " / ".join(fmt(x) for x in v)
    if isinstance(v, dict):
        return v.get("text") or v.get("code") or str(v)
    return f"{v:,}".replace(",", ".") if isinstance(v, int) and v >= 1000 else str(v)


def rows(q: dict) -> list[dict]:
    out = []
    p1a = q["part_1a"]
    for name, spec in p1a["context_factors"].items():
        out.append(meta(spec, scenario_id=f"1A-CTX-{name}", attributes=f"context: {name}", options=fmt(spec["levels"]),
                        displayed_values=fmt(spec["levels"])))
    for dist, cards in p1a["levels_by_distance"].items():
        for alt, attrs in cards.items():
            for attr, spec in attrs.items():
                out.append(meta(spec, scenario_id=f"1A-D{dist}-{alt}-{attr}", attributes=f"{alt}.{attr} @ {dist} km",
                                options="fixed per distance", displayed_values=fmt(spec["value"])))
    for name, spec in p1a["rotated_attributes"].items():
        out.append(meta(spec, scenario_id=f"1A-ROT-{name}", attributes=f"CAR_URBAN_POOL.{name}",
                        options=fmt(spec["levels"]), displayed_values=fmt(spec["levels"])))
    for pid, spec in p1a["price_variation_proposal"]["levels"].items():
        out.append(meta(spec, scenario_id=f"1A-PV-{pid}", attributes=spec["applies_to"], options=spec["rule"],
                        displayed_values=f"NOT SHOWN (proposal) — 14 km: {fmt(spec['example_14km_vnd'])}; "
                                         f"6 km: {fmt(spec['example_6km_vnd'])}"))
    p1b = q["part_1b"]
    pool = p1b["alternatives"]["CAR_INTERCITY_POOL"]
    for attr in ("seat_price_vnd", "fill_likelihood", "lead_days"):
        spec = pool[attr]
        vals = spec.get("levels", spec.get("value"))
        out.append(meta(spec, scenario_id=f"1B-POOL-{attr}", attributes=f"CAR_INTERCITY_POOL.{attr}",
                        options=fmt(vals), displayed_values=fmt(vals)))
    spec = p1b["alternatives"]["CAR_INTERCITY_PRIVATE"]["price_vnd"]
    out.append(meta(spec, scenario_id="1B-PRIVATE-price_vnd", attributes="CAR_INTERCITY_PRIVATE.price_vnd",
                    options="fixed", displayed_values=fmt(spec["value"])))
    out.append(meta(p1b["pairing"], scenario_id="1B-DESIGN-pairing", attributes="seat price x fill likelihood",
                    options=p1b["pairing"]["rule"], displayed_values="2 tasks per respondent"))
    h4 = q["part_2_h4"]
    for name, spec in h4["scenario"].items():
        shown = spec.get("value", {k: v for k, v in spec.items() if k not in ("source", "approval_status",
                                                                               "experimental_status", "derivation")})
        out.append(meta(spec, scenario_id=f"H4-SCENARIO-{name}", attributes=name, options="fixed",
                        displayed_values=fmt(shown)))
    for name, spec in h4["methods"].items():
        out.append(meta(spec, scenario_id=f"H4-METHOD-{name}", attributes="discount A / B",
                        options="shown as X/Y/Z, random order",
                        displayed_values=f"A −{spec['a_discount_pct']}% / B −{spec['b_discount_pct']}%"))
    for name, spec in q["part_3_demographics"].items():
        out.append(meta(spec, scenario_id=f"D-{name}", attributes=spec.get("question", name),
                        options=" | ".join(f"{o['code']}={o['text']}" for o in spec["options"]),
                        displayed_values=" | ".join(o["text"] for o in spec["options"])))
    for name, spec in q["quality_rules"].items():
        out.append(meta(spec, scenario_id=f"QC-{name}", attributes=spec["rule"], options=spec["action"],
                        displayed_values="not shown to respondents (published rule)"))
    qq = q["quotas"]
    out.append(meta(qq, scenario_id="QUOTA", attributes="valid respondents per group",
                    options=f"target {qq['target_valid_respondents']}, nominal {qq['nominal_per_group']}/group, "
                            f"share {qq['group_share']['min']}–{qq['group_share']['max']}",
                    displayed_values="group closed at session start when full"))
    return out


def main() -> None:
    q = yaml.safe_load(Q.read_text(encoding="utf-8"))
    table = rows(q)
    missing = [r["scenario_id"] for r in table if not r["source"] or not r["approval_status"]]
    if missing:
        sys.exit(f"rows without source / approval_status: {missing}")
    with CSV_OUT.open("w", newline="", encoding="utf-8") as fh:
        w = csv.DictWriter(fh, fieldnames=FIELDS)
        w.writeheader()
        w.writerows(table)
    counts: dict[str, int] = {}
    for r in table:
        counts[r["approval_status"]] = counts.get(r["approval_status"], 0) + 1
    lines = ["# Khảo sát S1 — Bảng kịch bản đầy đủ", "",
             f"Sinh tự động bởi `scripts/survey/scenario_table.py` từ `survey/s1/questionnaire.draft.yaml` "
             f"(`draft_version` {q['draft_version']}) — cùng tệp API dùng để sinh thiết kế. Bản CSV: `survey/s1/scenario_table.csv`.",
             "", "Tổng hợp `approval_status`: " + ", ".join(f"`{k}` {v}" for k, v in sorted(counts.items())), "",
             "| " + " | ".join(FIELDS) + " |", "|" + "---|" * len(FIELDS)]
    for r in table:
        lines.append("| " + " | ".join(str(r[f]).replace("|", "/").replace("\n", " ") for f in FIELDS) + " |")
    MD_OUT.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(f"{len(table)} rows -> {CSV_OUT.relative_to(ROOT)}, {MD_OUT.relative_to(ROOT)}; {counts}")


if __name__ == "__main__":
    main()
