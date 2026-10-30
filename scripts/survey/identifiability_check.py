"""SURVEY-06: identifiability of the Part-1A discrete-choice experiment.

A conditional logit identifies coefficients only from differences between the
alternatives of the same task. For each design this builds those differences
(versus CAR_URBAN_PRIVATE) over all 6 blocks x 8 tasks and reports the rank, the
pairwise correlations and the variance inflation factors (VIF) of the attribute
columns. Designs:
  A  base levels (variation design off): prices / times change only with distance
  B  proposal: pool discount d in {0.20, 0.25, 0.35} and private / bike price
     multipliers {0.90, 1.00, 1.10}, rotated independently of distance
  C  proposal B + one travel-time multiplier {0.85, 1.00, 1.15} for all modes
  D  proposal B + independent time multipliers per mode {0.80, 1.00, 1.20}
     (car and motorbike times vary separately, e.g. traffic / parking)
  generator_inactive / generator_active  the real generator with the questionnaire's
     variation design off / on (on = the file's design, D2 since draft 5)
B / C / D here are hand-built comparison designs. Pool prices in B / C
are recomputed from the displayed private price P with the Baseline rules
(expected = floor((1 - d) P), Quote = floor(0.80 P), Unmatched = floor(Quote +
0.5 (P - Quote))), and every level is checked against the Baseline bounds.

Usage (repo root): python -I scripts/survey/identifiability_check.py
"""

import itertools
import json
import math
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "docs" / "implementation" / "survey" / "evidence" / "s1_identifiability.json"
BASE = {14: {"bike_p": 81000, "bike_t": 35, "priv_p": 194000, "priv_t": 40, "detour": 12},
        6: {"bike_p": 41000, "bike_t": 16, "priv_p": 95000, "priv_t": 19, "detour": 6}}
LIKELIHOOD = ["HIGH", "MEDIUM", "LOW"]
WALK = [0, 200]
D_MIN, D_MAX, ALPHA = 0.20, 0.60, 0.50          # Baseline car_urban
COLUMNS = ["asc_bike", "asc_pool", "price_k", "time_min", "detour_min", "unmatched_gap_k",
           "like_medium", "like_low", "walk_200"]


def floor_k(v: float) -> int:
    return int(v // 1000) * 1000


def pool_prices(p: int, d: float) -> tuple[int, int, int]:
    quote = floor_k(p * (1 - D_MIN))
    return floor_k(p * (1 - d)), quote, floor_k(quote + ALPHA * (p - quote))


def rows_for(design: str) -> tuple[list[list[float]], list[dict]]:
    rows, checks = [], []
    contexts = list(itertools.product([6, 14], ["sun", "rain"], ["urgent", "relaxed"]))
    combos = list(itertools.product(LIKELIHOOD, WALK))
    levels3 = [0, 1, 2]
    for block in range(6):
        for i, (dist, _w, _u) in enumerate(contexts):
            b = BASE[dist]
            lik, walk = combos[(i + 2 * (block % 3)) % 6]
            d, mp, mb, mt = 0.25, 1.0, 1.0, 1.0
            mtb = None
            if design in ("B", "C", "D"):
                d = [0.20, 0.25, 0.35][levels3[(i + block) % 3]]
                mp = [0.90, 1.00, 1.10][levels3[(i + 2 * block + 1) % 3]]
                mb = [0.90, 1.00, 1.10][levels3[(2 * i + block + 2) % 3]]
            if design == "C":
                mt = [0.85, 1.00, 1.15][levels3[(i + block // 2) % 3]]
            if design == "D":
                mt = [0.80, 1.00, 1.20][levels3[(i + block // 2) % 3]]
                mtb = [0.80, 1.00, 1.20][levels3[(2 * i + block // 3 + 1) % 3]]
            priv_p = floor_k(b["priv_p"] * mp)
            bike_p = floor_k(b["bike_p"] * mb)
            priv_t, bike_t = round(b["priv_t"] * mt), round(b["bike_t"] * (mtb or mt))
            detour = round(b["detour"] * mt)
            exp_p, quote, unm = pool_prices(priv_p, d)
            checks.append({"dist": dist, "d": d, "priv_p": priv_p, "expected": exp_p, "quote": quote, "unmatched": unm,
                           "ok": D_MIN <= d <= D_MAX and exp_p <= quote < unm < priv_p
                           and floor_k(priv_p * (1 - D_MAX)) <= exp_p})
            # bike - private
            rows.append([1, 0, (bike_p - priv_p) / 1000, bike_t - priv_t, 0, 0, 0, 0, 0])
            # pool - private (pool rides the private route + at most `detour` minutes)
            rows.append([0, 1, (exp_p - priv_p) / 1000, 0, detour, (unm - exp_p) / 1000,
                         int(lik == "MEDIUM"), int(lik == "LOW"), int(walk == 200)])
    return rows, checks


def rows_generated(active: bool) -> tuple[list[list[float]], list[dict]]:
    """Rows from the REAL generator (backend survey_design.build_design) over the 6 blocks,
    with the questionnaire's variation design forced on/off in memory only."""
    import copy
    import uuid

    import yaml

    sys.path.insert(0, str(ROOT / "backend"))
    from app.modules.ml_models.survey_design import build_design  # noqa: PLC0415

    q = copy.deepcopy(yaml.safe_load((ROOT / "survey" / "s1" / "questionnaire.draft.yaml").read_text(encoding="utf-8")))
    q["part_1a"]["variation_design"]["active"] = active
    rows, checks = [], []
    for block in range(6):
        d = build_design(q, uuid.UUID(int=block + 1), block)
        for t in d["tasks"]:
            if t["part"] != "1A":
                continue
            c = {x["alternative"]: x for x in t["cards"]}
            bike, pool, priv = c["BIKE_URBAN"], c["CAR_URBAN_POOL"], c["CAR_URBAN_PRIVATE"]
            checks.append({"ok": pool["price_vnd"] <= pool["quote_cap_vnd"] < pool["max_price_if_unmatched_vnd"]
                           < priv["price_vnd"] and pool["price_vnd"] >= floor_k(priv["price_vnd"] * (1 - D_MAX))})
            rows.append([1, 0, (bike["price_vnd"] - priv["price_vnd"]) / 1000, bike["travel_min"] - priv["travel_min"],
                         0, 0, 0, 0, 0])
            rows.append([0, 1, (pool["price_vnd"] - priv["price_vnd"]) / 1000, 0, pool["max_detour_min"],
                         (pool["max_price_if_unmatched_vnd"] - pool["price_vnd"]) / 1000,
                         int(pool["match_likelihood"] == "MEDIUM"), int(pool["match_likelihood"] == "LOW"),
                         int(pool["walk_m"] == 200)])
    return rows, checks


def corr(a: list[float], b: list[float]) -> float | None:
    n = len(a)
    ma, mb = sum(a) / n, sum(b) / n
    va = sum((x - ma) ** 2 for x in a)
    vb = sum((y - mb) ** 2 for y in b)
    if va == 0 or vb == 0:
        return None
    return sum((x - ma) * (y - mb) for x, y in zip(a, b, strict=True)) / math.sqrt(va * vb)


def rank(m: list[list[float]], eps: float = 1e-9) -> int:
    a = [r[:] for r in m]
    r = 0
    for c in range(len(a[0])):
        piv = max(range(r, len(a)), key=lambda i: abs(a[i][c]), default=None)
        if piv is None or abs(a[piv][c]) < eps:
            continue
        a[r], a[piv] = a[piv], a[r]
        for i in range(len(a)):
            if i != r and abs(a[i][c]) > eps:
                f = a[i][c] / a[r][c]
                a[i] = [x - f * y for x, y in zip(a[i], a[r], strict=True)]
        r += 1
        if r == len(a):
            break
    return r


def inverse(m: list[list[float]]) -> list[list[float]] | None:
    n = len(m)
    a = [row[:] + [float(i == j) for j in range(n)] for i, row in enumerate(m)]
    for c in range(n):
        piv = max(range(c, n), key=lambda i: abs(a[i][c]))
        if abs(a[piv][c]) < 1e-10:
            return None
        a[c], a[piv] = a[piv], a[c]
        p = a[c][c]
        a[c] = [x / p for x in a[c]]
        for i in range(n):
            if i != c:
                f = a[i][c]
                a[i] = [x - f * y for x, y in zip(a[i], a[c], strict=True)]
    return [row[n:] for row in a]


def analyse(design: str) -> dict:
    if design == "generator_inactive":
        rows, checks = rows_generated(False)
    elif design == "generator_active":
        rows, checks = rows_generated(True)
    else:
        rows, checks = rows_for(design)
    cols = list(zip(*rows, strict=True))
    attrs = [k for k in range(2, len(COLUMNS))]  # VIF on attribute columns (ASCs are intercept-like)
    r = [[corr(cols[i], cols[j]) or 0.0 for j in attrs] for i in attrs]
    inv = inverse(r)
    vif = {COLUMNS[k]: (None if inv is None else round(inv[n][n], 1)) for n, k in enumerate(attrs)}
    return {"design": design, "rows": len(rows), "columns": COLUMNS, "rank": rank(rows), "full_rank": len(COLUMNS),
            "identified": rank(rows) == len(COLUMNS) and inv is not None and max(vif.values()) < 10,
            "corr_price_time": round(corr(cols[2], cols[3]) or 0, 3),
            "corr_price_detour": round(corr(cols[2], cols[4]) or 0, 3),
            "corr_price_unmatched_gap": round(corr(cols[2], cols[5]) or 0, 3),
            "vif": vif, "max_vif": None if inv is None else max(v for v in vif.values() if v is not None),
            "feasibility": {"levels_checked": len(checks), "all_within_baseline_bounds": all(c["ok"] for c in checks),
                            "violations": [c for c in checks if not c["ok"]][:5]}}


def main() -> None:
    results = [analyse(d) for d in ("A", "B", "C", "D", "generator_inactive", "generator_active")]
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(results, ensure_ascii=False, indent=2), encoding="utf-8")
    sys.stdout.reconfigure(encoding="utf-8")
    for r in results:
        print(f"design {r['design']}: rank {r['rank']}/{r['full_rank']}, max VIF {r['max_vif']}, "
              f"corr(price,time) {r['corr_price_time']}, corr(price,detour) {r['corr_price_detour']}, "
              f"corr(price,unmatched gap) {r['corr_price_unmatched_gap']}, identified={r['identified']}, "
              f"feasible={r['feasibility']['all_within_baseline_bounds']}")
        print("   VIF", r["vif"])


if __name__ == "__main__":
    main()
