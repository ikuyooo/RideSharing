"""Survey S1 experimental design (pure, deterministic per respondent).

Built only from survey/s1/questionnaire.draft.yaml; values marked TBD are shown
as pending and never replaced by invented numbers (owner decision P1-D5).

Part 1A: full factorial of the three Section 65.2 context factors (2x2x2 = 8
tasks), random order per respondent. The pool card's rotated attributes
(match likelihood x walk = 6 combinations) follow a block rotation:
combo(context i, block k) = (i + 2(k mod 3)) mod 6, so the three rotations start
at different combinations. Part 1B pairs the two seat prices with the two
hypothetical fill-likelihood levels; block k // 3 selects which pairing, so both
pairings appear equally across the 6 blocks. Card positions are shuffled per task.
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


def build_design(q: dict[str, Any], respondent_id: uuid.UUID, block: int) -> dict[str, Any]:
    rng = random.Random(respondent_id.int)
    p1a = q["part_1a"]
    factors = p1a["context_factors"]
    contexts = list(itertools.product(*(factors[k]["levels"] for k in ("distance_km", "weather", "urgency"))))
    rotated = p1a["rotated_attributes"]
    combos = list(itertools.product(rotated["match_likelihood"]["levels"], rotated["walk_m"]["levels"]))

    tasks_1a = []
    for i, (distance, weather, urgency) in enumerate(contexts):
        levels = p1a["levels_by_distance"][str(distance)]
        likelihood, walk = combos[(i + 2 * (block % 3)) % len(combos)]
        cards = [
            {"alternative": "BIKE_URBAN", "label": p1a["alternatives"]["BIKE_URBAN"]["label"],
             "price_vnd": _value(levels["BIKE_URBAN"]["price_vnd"]), "travel_min": _value(levels["BIKE_URBAN"]["travel_min"])},
            {"alternative": "CAR_URBAN_POOL", "label": p1a["alternatives"]["CAR_URBAN_POOL"]["label"],
             "price_vnd": _value(levels["CAR_URBAN_POOL"]["expected_price_vnd"]),
             "max_price_if_unmatched_vnd": _value(levels["CAR_URBAN_POOL"]["max_price_if_unmatched_vnd"]),
             "max_detour_min": _value(levels["CAR_URBAN_POOL"]["max_detour_min"]),
             "match_likelihood": LIKELIHOOD_CODES[likelihood], "walk_m": walk},
            {"alternative": "CAR_URBAN_PRIVATE", "label": p1a["alternatives"]["CAR_URBAN_PRIVATE"]["label"],
             "price_vnd": _value(levels["CAR_URBAN_PRIVATE"]["price_vnd"]),
             "travel_min": _value(levels["CAR_URBAN_PRIVATE"]["travel_min"])},
        ]
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
        fill = fill_levels[(j + block // 3) % len(fill_levels)]
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
