"""Fixed fares needed by hard constraint 8 (budget cap) in Phase 2. Pure functions over
one `pricing_configs.params_json` section; amounts are integer VND floored to the
1.000 VND rounding step (D-18, D-48).

  BikeFare     = floor((BASE + PER_KM x km + PER_MIN x min) / 1000) x 1000      (Section 10.1)
  PrivateFare  = floor((BASE + PER_KM x km + PER_MIN x min) / 1000) x 1000      (Section 12.1)
  Quote_i      = floor(P_i x (1 - d_min) / 1000) x 1000                          (Section 18.3)
  Unmatched_i  = floor((Quote_i + alpha x (P_i - Quote_i)) / 1000) x 1000        (Section 18.3)
  PlanFare     = BASE + PER_KM x D_plan + PER_MIN x T_plan + STOP_FEE x extra    (Section 13)

The pool allocation (Floor / Cap, D1-D6, gates 1-2) is Phase 3.
"""

from collections.abc import Mapping
from dataclasses import dataclass
from typing import Any


def _floor_step(amount: float, step: int) -> int:
    # round() first: guards against a binary floating-point result a hair below a step.
    return int(round(amount, 6) // step) * step


def distance_time_fare(section: Mapping[str, Any], km: float, minutes: float) -> int:
    raw = section["base_vnd"] + section["per_km_vnd"] * km + section["per_min_vnd"] * minutes
    return _floor_step(raw, int(section["rounding_step_vnd"]))


@dataclass(frozen=True)
class PoolQuote:
    private_fare: int   # P_i
    quote: int          # Quote_i, cap if matched
    unmatched: int      # Unmatched_i, the most the rider can pay (constraint 8)


def pool_quote(car_urban: Mapping[str, Any], private_fare: int) -> PoolQuote:
    step = int(car_urban["rounding_step_vnd"])
    quote = _floor_step(private_fare * (1 - car_urban["d_min"]), step)
    unmatched = _floor_step(quote + car_urban["unmatched_passenger_share_alpha"] * (private_fare - quote), step)
    return PoolQuote(private_fare=private_fare, quote=quote, unmatched=unmatched)
