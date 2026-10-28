"""Survey S1 experimental design (pure, deterministic per respondent).

Built only from survey/s1/questionnaire.draft.yaml; values marked TBD are shown
as pending and never replaced by invented numbers (owner decision P1-D5).

Part 1A: full factorial of the three Section 65.2 context factors (2x2x2 = 8
tasks), random order per respondent. The pool card's rotated attributes
(match likelihood x walk = 6 combinations) follow a block rotation:
combo(context i, block k) = (i + 2(k mod 3)) mod 6, so the three rotations start
at different combinations. Part 1B rotates the three hypothetical fill-likelihood levels
over the two seat prices with (task + block) mod 3, so across the 6 blocks every seat
price meets every level twice (orthogonal - the level is not tied to the price). Card positions are shuffled per task.

Variation design (SURVEY-06, `part_1a.variation_design`): when - and only when - the
owner activates it, each Part-1A task gets its own pool discount d, private / bike
price multipliers and per-mode time multipliers, rotated independently of the
distance; every displayed pool price is then recomputed from the displayed private
price with the locked Baseline rules (expected = floor((1 - d) P), cap = Quote =
floor((1 - d_min) P), unmatched = floor(Quote + alpha (P - Quote))). Inactive: the
base levels of `levels_by_distance` are shown unchanged.
"""

import itertools
import random
import uuid
from typing import Any

TBD = "TBD"
LIKELIHOOD_CODES = {"Cao": "HIGH", "Trung bình": "MEDIUM", "Thấp": "LOW"}
FAIRNESS_LABELS = ("X", "Y", "Z")
N_BLOCKS = 6  # 3 Part-1A rotations x 2 Part-1B pairings


def _value(spec: Any) -> Any:
    """{value, source} -> value; TBD stays TBD."""
    if isinstance(spec, dict) and "value" in spec:
        return spec["value"]
    return TBD


def _floor_k(v: float) -> int:
    return int(v // 1000) * 1000


def variation_levels(spec: dict[str, Any], i: int, block: int) -> dict[str, float]:
    """Level of every varied factor for context i in block `block` (rotation rules from
    the questionnaire: level index = (a * i + b * block + c) mod n, with block // m for
    the slower factors)."""
    out = {}
    for name, f in spec["factors"].items():
        k = block // f.get("block_div", 1)
        out[name] = f["levels"][(f["a"] * i + f["b"] * k + f["c"]) % len(f["levels"])]
    return out


def varied_cards(levels: dict[str, Any], v: dict[str, float], bounds: dict[str, float]) -> dict[str, Any]:
    """Displayed values of one Part-1A task under the variation design."""
    p = _floor_k(_value(levels["CAR_URBAN_PRIVATE"]["price_vnd"]) * v["private_price_mult"])
    quote = _floor_k(p * (1 - bounds["d_min"]))
    expected = _floor_k(p * (1 - v["pool_discount_d"]))
    unmatched = _floor_k(quote + bounds["alpha"] * (p - quote))
    if not (bounds["d_min"] <= v["pool_discount_d"] <= bounds["d_max"] and expected <= quote < unmatched < p):
        raise ValueError(f"variation level outside the Baseline bounds: {v}")
    return {"bike_price": _floor_k(_value(levels["BIKE_URBAN"]["price_vnd"]) * v["bike_price_mult"]),
            "bike_min": round(_value(levels["BIKE_URBAN"]["travel_min"]) * v["bike_time_mult"]),
            "private_price": p, "private_min": round(_value(levels["CAR_URBAN_PRIVATE"]["travel_min"]) * v["car_time_mult"]),
            "pool_expected": expected, "pool_quote": quote, "pool_unmatched": unmatched,
            "pool_detour": round(_value(levels["CAR_URBAN_POOL"]["max_detour_min"]) * v.get("detour_mult", v["car_time_mult"]))}


def build_design(q: dict[str, Any], respondent_id: uuid.UUID, block: int) -> dict[str, Any]:
    rng = random.Random(respondent_id.int)
    p1a = q["part_1a"]
    factors = p1a["context_factors"]
    contexts = list(itertools.product(*(factors[k]["levels"] for k in ("distance_km", "weather", "urgency"))))
    rotated = p1a["rotated_attributes"]
    combos = list(itertools.product(rotated["match_likelihood"]["levels"], rotated["walk_m"]["levels"]))

    vd = p1a.get("variation_design", {})
    active = bool(vd.get("active"))
    tasks_1a = []
    for i, (distance, weather, urgency) in enumerate(contexts):
        levels = p1a["levels_by_distance"][str(distance)]
        likelihood, walk = combos[(i + 2 * (block % 3)) % len(combos)]
        varied = varied_cards(levels, variation_levels(vd, i, block), vd["baseline_bounds"]) if active else None
        cards = [
            {"alternative": "BIKE_URBAN", "label": p1a["alternatives"]["BIKE_URBAN"]["label"],
             "price_vnd": _value(levels["BIKE_URBAN"]["price_vnd"]), "travel_min": _value(levels["BIKE_URBAN"]["travel_min"])},
            {"alternative": "CAR_URBAN_POOL", "label": p1a["alternatives"]["CAR_URBAN_POOL"]["label"],
             "price_vnd": _value(levels["CAR_URBAN_POOL"]["expected_price_vnd"]),
             "quote_cap_vnd": _value(levels["CAR_URBAN_POOL"]["quote_cap_vnd"]),
             "max_price_if_unmatched_vnd": _value(levels["CAR_URBAN_POOL"]["max_price_if_unmatched_vnd"]),
             "max_detour_min": _value(levels["CAR_URBAN_POOL"]["max_detour_min"]),
             "match_likelihood": LIKELIHOOD_CODES[likelihood], "walk_m": walk},
            {"alternative": "CAR_URBAN_PRIVATE", "label": p1a["alternatives"]["CAR_URBAN_PRIVATE"]["label"],
             "price_vnd": _value(levels["CAR_URBAN_PRIVATE"]["price_vnd"]),
             "travel_min": _value(levels["CAR_URBAN_PRIVATE"]["travel_min"])},
        ]
        if varied:
            bike, pool, private = cards
            bike |= {"price_vnd": varied["bike_price"], "travel_min": varied["bike_min"]}
            private |= {"price_vnd": varied["private_price"], "travel_min": varied["private_min"]}
            pool |= {"price_vnd": varied["pool_expected"], "quote_cap_vnd": varied["pool_quote"],
                     "max_price_if_unmatched_vnd": varied["pool_unmatched"], "max_detour_min": varied["pool_detour"]}
        rng.shuffle(cards)
        for pos, card in enumerate(cards, start=1):
            card["position"] = pos
        tasks_1a.append({"part": "1A", "task_id": f"1A-d{distance}-{'rain' if 'Mưa' in weather else 'sun'}-"
                                                  f"{'urgent' if 'đúng giờ' in urgency else 'relaxed'}",
                         "context": {"distance_km": distance, "weather": weather, "urgency": urgency}, "cards": cards})
    rng.shuffle(tasks_1a)

    p1b = q["part_1b"]
    pool_b = p1b["alternatives"]["CAR_INTERCITY_POOL"]
    tasks_1b = []
    fill_levels = pool_b["fill_likelihood"]["levels"]
    for j, seat_price in enumerate(pool_b["seat_price_vnd"]["levels"]):
        fill = fill_levels[(j + block) % len(fill_levels)]
        cards = [
            {"alternative": "CAR_INTERCITY_POOL", "label": pool_b["label"], "price_vnd": seat_price,
             "fill_likelihood": fill["code"], "fill_likelihood_text": fill["text"],
             "lead_days": pool_b["lead_days"]["value"]},
            {"alternative": "CAR_INTERCITY_PRIVATE", "label": p1b["alternatives"]["CAR_INTERCITY_PRIVATE"]["label"],
             "price_vnd": p1b["alternatives"]["CAR_INTERCITY_PRIVATE"]["price_vnd"]["value"]},
            {"alternative": "OTHER", "label": p1b["alternatives"]["OTHER"]["label"]},
        ]
        rng.shuffle(cards)
        for pos, card in enumerate(cards, start=1):
            card["position"] = pos
        tasks_1b.append({"part": "1B", "task_id": f"1B-seat{seat_price}", "cards": cards})
    rng.shuffle(tasks_1b)

    methods = list(q["part_2_h4"]["methods"].items())
    rng.shuffle(methods)
    fairness = [{"display_label": label, "display_position": pos, "method": name,
                 "a_discount_pct": m["a_discount_pct"], "b_discount_pct": m["b_discount_pct"]}
                for pos, (label, (name, m)) in enumerate(zip(FAIRNESS_LABELS, methods, strict=True), start=1)]

    for index, task in enumerate(tasks_1a + tasks_1b, start=1):
        task["task_index"] = index
    return {"block": block, "tasks": tasks_1a + tasks_1b, "fairness": fairness,
            "scenario": {k: _value(v) if isinstance(v, dict) and "value" in v else v
                         for k, v in q["part_2_h4"]["scenario"].items()}}
