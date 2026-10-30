"""SURVEY-06 / OWNER APPROVAL s.4: statistical diagnostics of the Part-1A design as the
conditional logit sees it (columns: app.modules.ml_models.survey_stats.COLUMNS).

For the designs the REAL generator produces (6 blocks x 8 tasks = 48 choice sets) with
the variation design off (base levels) and on: matrix D2 (active local design) and the
superseded matrix D (in memory only):
  rank of the within-task difference matrix (ASCs + attributes + context interactions)
  VIF of the attribute columns, condition number of the scaled information matrix,
  D0-error (zero priors) and Dp-error (illustrative priors, an assumption)
  correlations of price / time / distance / mode at alternative level
  level balance of every varied factor, display consistency of every pool card
  dominance / obvious-choice screening
Writes docs/implementation/survey/evidence/s1_design_diagnostics.json.

Usage (repo root): python -I scripts/survey/design_diagnostics.py
"""

import copy
import json
import sys
import uuid
from collections import Counter
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "backend"))
from app.modules.ml_models import survey_stats as st  # noqa: E402
from app.modules.ml_models.survey_design import build_design, variation_levels  # noqa: E402

OUT = ROOT / "docs" / "implementation" / "survey" / "evidence" / "s1_design_diagnostics.json"


def floor_k(v: float) -> int:
    return int(v // 1000) * 1000


def designs(q: dict, active: bool) -> list[tuple[int, int, dict]]:
    q = copy.deepcopy(q)
    q["part_1a"]["variation_design"]["active"] = active
    out = []
    contexts_index = {}
    for i, ctx in enumerate(__import__("itertools").product(
            *(q["part_1a"]["context_factors"][k]["levels"] for k in ("distance_km", "weather", "urgency")))):
        contexts_index[ctx] = i
    for block in range(6):
        for t in build_design(q, uuid.UUID(int=block + 1), block)["tasks"]:
            if t["part"] == "1A":
                c = t["context"]
                out.append((block, contexts_index[(c["distance_km"], c["weather"], c["urgency"])], t))
    return out


def analyse(q: dict, active: bool) -> dict:
    tasks = designs(q, active)
    sets = [st.encode(t) for _, _, t in tasks]
    diffs = [[a - b for a, b in zip(row, xs[-1], strict=True)] for xs in sets for row in xs[:-1]]
    info0 = st.information(sets, [0.0] * len(st.COLUMNS))
    infop = st.information(sets, st.PRIORS)
    # alternative-level correlations
    alt_rows = [(t["context"]["distance_km"], alt, row) for _, _, t in tasks for alt, row in zip(st.ALTERNATIVES, st.encode(t), strict=True)]
    def col(name: str, rows: list) -> list[float]:
        return [r[2][st.COLUMNS.index(name)] for r in rows]
    corr_all = {"price_vs_time": st.corr(col("price_k", alt_rows), col("time_min", alt_rows)),
                "price_vs_distance": st.corr(col("price_k", alt_rows), [r[0] for r in alt_rows]),
                "time_vs_distance": st.corr(col("time_min", alt_rows), [r[0] for r in alt_rows]),
                "price_vs_is_bike": st.corr(col("price_k", alt_rows), [float(r[1] == "BIKE_URBAN") for r in alt_rows])}
    within = {}
    for alt in ("BIKE_URBAN", "CAR_URBAN_PRIVATE", "CAR_URBAN_POOL"):
        rows = [r for r in alt_rows if r[1] == alt]
        within[alt] = {"price_vs_distance": st.corr(col("price_k", rows), [r[0] for r in rows]),
                       "time_vs_distance": st.corr(col("time_min", rows), [r[0] for r in rows]),
                       "price_vs_time": st.corr(col("price_k", rows), col("time_min", rows))}
    # level balance and display consistency
    vd = q["part_1a"]["variation_design"]
    balance: dict[str, Counter] = {}
    consistent, checked = 0, 0
    for block, i, t in tasks:
        levels = variation_levels(vd, i, block) if active else {}
        for name, v in levels.items():
            balance.setdefault(name, Counter())[(t["context"]["distance_km"], v)] += 1
        c = {x["alternative"]: x for x in t["cards"]}
        pool, priv = c["CAR_URBAN_POOL"], c["CAR_URBAN_PRIVATE"]
        balance.setdefault("match_likelihood", Counter())[pool["match_likelihood"]] += 1
        balance.setdefault("walk_m", Counter())[pool["walk_m"]] += 1
        d = levels.get("pool_discount_d", 0.25)
        p = priv["price_vnd"]
        quote = floor_k(p * 0.80)
        checked += 1
        consistent += (pool["price_vnd"] == floor_k(p * (1 - d)) and pool["quote_cap_vnd"] == quote
                       and pool["max_price_if_unmatched_vnd"] == floor_k(quote + 0.5 * (p - quote)))
    # dominance / obvious choices
    bike_dominates_private = sum(1 for _, _, t in tasks if (lambda c: c["BIKE_URBAN"]["price_vnd"] <= c["CAR_URBAN_PRIVATE"]["price_vnd"]
                                 and c["BIKE_URBAN"]["travel_min"] <= c["CAR_URBAN_PRIVATE"]["travel_min"])(
                                 {x["alternative"]: x for x in t["cards"]}))
    private_dominates_pool = sum(1 for _, _, t in tasks if (lambda c: c["CAR_URBAN_PRIVATE"]["price_vnd"] <= c["CAR_URBAN_POOL"]["price_vnd"])(
                                 {x["alternative"]: x for x in t["cards"]}))
    obvious = sum(1 for xs in sets if max(st.probabilities(xs, st.PRIORS)) > 0.9)
    speeds = sorted({round(t["context"]["distance_km"] / (x["travel_min"] / 60), 1) for _, _, t in tasks
                     for x in t["cards"] if x.get("travel_min")})
    v = st.vif(sets)
    return {
        "variation_design_active": active, "choice_sets": len(sets), "columns": st.COLUMNS,
        "rank_of_difference_matrix": st.rank(diffs), "parameters": len(st.COLUMNS),
        "max_vif": None if None in v.values() else max(v.values()), "vif": v,
        "condition_number_info_zero_priors": st.condition_number(info0),
        "condition_number_info_priors": st.condition_number(infop),
        "d0_error": st.d_error(sets, [0.0] * len(st.COLUMNS)), "dp_error": st.d_error(sets, st.PRIORS),
        "priors_assumption": dict(zip(st.COLUMNS, st.PRIORS, strict=True)),
        "correlations_alternative_level": {k: None if x is None else round(x, 3) for k, x in corr_all.items()},
        "correlations_within_alternative": {a: {k: None if x is None else round(x, 3) for k, x in d.items()} for a, d in within.items()},
        "level_balance": {k: {str(kk): vv for kk, vv in sorted(c.items(), key=str)} for k, c in balance.items()},
        "pool_display_consistent": f"{consistent}/{checked}",
        "dominance": {"bike_cheaper_and_not_slower_than_private": bike_dominates_private,
                      "private_not_dearer_than_pool": private_dominates_pool,
                      "choice_sets_with_max_probability_above_0_9_under_priors": obvious},
        "implied_speeds_kmh": speeds,
    }


def expected_t(q: dict, n_respondents: int = 150) -> dict:
    """|prior| / expected SE at N respondents (each block used by N / 6), full and lean spec."""
    import math

    sets = [st.encode(t) for _, _, t in designs(q, True)]
    out = {}
    for spec, drop in (("full", set()), ("lean_without_urgent_x_time", {"urgent_x_time"})):
        keep = [i for i, c in enumerate(st.COLUMNS) if c not in drop]
        pri = [st.PRIORS[i] for i in keep]
        info = st.information([[[row[i] for i in keep] for row in xs] for xs in sets], pri)
        inv = st.inverse([[x * n_respondents / 6 for x in r] for r in info])
        out[spec] = {st.COLUMNS[k]: round(abs(p) / math.sqrt(inv[j][j]), 2) for j, (k, p) in enumerate(zip(keep, pri, strict=True))}
    return out


def with_superseded(q: dict, name: str) -> dict:
    q = copy.deepcopy(q)
    q["part_1a"]["variation_design"]["factors"] = copy.deepcopy(q["part_1a"]["superseded_designs"][name]["factors"])
    return q


def main() -> None:
    q = yaml.safe_load((ROOT / "survey" / "s1" / "questionnaire.draft.yaml").read_text(encoding="utf-8"))
    d = with_superseded(q, "D")
    active = q["part_1a"]["variation_design"]["design"]
    res = [analyse(q, False), analyse(d, True) | {"design": "D (superseded)", "expected_abs_t_n150": expected_t(d)},
           analyse(q, True) | {"design": f"{active} (active, local TEST design)", "expected_abs_t_n150": expected_t(q),
                               "expected_abs_t_n300": expected_t(q, 300)}]
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(res, ensure_ascii=False, indent=2, default=str), encoding="utf-8")
    sys.stdout.reconfigure(encoding="utf-8")
    for r in res:
        print(json.dumps({k: v for k, v in r.items() if k not in ("columns", "priors_assumption", "level_balance")},
                         ensure_ascii=False, default=str))
        print("level balance:", json.dumps(r["level_balance"], ensure_ascii=False))


if __name__ == "__main__":
    main()
