"""PoolPricingCheck - steps 4-5 of Section 36 for branch A (insertion into an open pool plan),
the Phase 3 implementation of the `pooling.insertion.PricingCheck` interface of Phase 2.

Called once per insertion option that passed the 11 hard constraints. It measures the new plan
(D_plan, T_plan from S_0 - `pooling.insertion.plan_extent`, DD-P3-04), builds the pricing input
of every booking of the plan (frozen group L, unlocked group U_old, the new rider) and runs
D1-D6 (`pricing.pool.price_insertion`). The outcome of each option is kept so the generator can
attach the accepted allocation to the candidate.

A plan whose stored pricing state is missing or inconsistent is rejected with a precise reason
and never priced from guesses."""

from dataclasses import dataclass, field
from datetime import datetime
from fractions import Fraction

from app.modules.candidate.constraints import Violation
from app.modules.pooling.insertion import InsertionResult, plan_extent
from app.modules.pooling.pricing_state import PlanPricingState
from app.modules.pricing.money import q
from app.modules.pricing.params import CarUrbanParams
from app.modules.pricing.pool import InsertionInput, PoolPricing, PoolRider, PricedRider, price_insertion

LOCKED = "MATCHED_LOCKED"
UNLOCKED = "POOL_SEARCHING"
NEW_REF = "new"


def _detour(ride_m: float, direct_m: float) -> Fraction:
    return max(Fraction(0), (q(ride_m) - q(direct_m)) / q(direct_m))


@dataclass
class PoolPricingCheck:
    car: CarUrbanParams
    state: PlanPricingState
    new_private_fare: int
    new_seats: int
    new_direct_duration_s: float
    new_budget_max: int | None
    now: datetime
    completed_stops: int
    outcomes: dict[tuple[int, int], PoolPricing] = field(default_factory=dict)

    def _state_error(self) -> str | None:
        s = self.state
        if s.pricing_version is None:
            return "plan has no pricing_version"
        if self.completed_stops > 0 and s.started_at is None:
            return "running plan has no started_at"
        for part in s.participants:
            if part.private_fare is None or part.direct_duration_s is None or part.direct_distance_m is None:
                return f"participant {part.booking_id} lacks P_i or its direct trip"
            if part.price_status not in (LOCKED, UNLOCKED):
                return f"participant {part.booking_id} has price_status {part.price_status}"
            if part.dropped_off and part.price_status != LOCKED:
                return f"participant {part.booking_id} was dropped off without a locked price"
        return None

    def __call__(self, result: InsertionResult) -> Violation | None:
        err = self._state_error()
        if err is not None:
            return Violation("P3_PLAN_PRICING_STATE", "plan", err)
        sim = result.simulation
        if sim is None:
            return Violation("P3_PLAN_PRICING_STATE", "plan", "insertion result without simulation")
        started = self.completed_stops > 0
        d_m, t_s = (q(x) for x in plan_extent(sim, started))
        if started:
            d_m += q(self.state.driven_m_since_start)
            t_s += q((self.now - self.state.started_at).total_seconds())  # type: ignore[operator]
        riders = {r.ref: r for r in result.evaluation.riders}
        new = riders[NEW_REF]
        old = []
        overlap = False
        for part in self.state.participants:
            ref = str(part.booking_id)
            outcome = riders.get(ref)
            detour = _detour(outcome.ride_distance_m, outcome.direct_distance_m) if outcome else Fraction(0)
            if outcome is not None and max(outcome.span[0], new.span[0]) < min(outcome.span[1], new.span[1]):
                overlap = True
            old.append(PricedRider(
                rider=PoolRider(ref, part.private_fare, part.seats, q(part.direct_duration_s), detour),  # type: ignore[arg-type]
                locked=part.price_status == LOCKED, fare_exact_old=part.fare_exact,
                fare_charged_old=part.fare_charged, final_price=part.final_price))
        x = InsertionInput(
            plan_open=self.state.status == "PLAN_OPEN_SEARCHING", plan_fare_old=self.state.plan_fare_exact, old=old,
            new=PoolRider(NEW_REF, self.new_private_fare, self.new_seats, q(self.new_direct_duration_s),
                          _detour(new.ride_distance_m, new.direct_distance_m)),
            new_budget_max=self.new_budget_max, co_riding_overlap=overlap, d_plan_m=d_m, t_plan_s=t_s,
            total_stops=self.completed_stops + len(result.chain))
        priced = price_insertion(self.car, x)
        self.outcomes[(result.p_idx, result.q_idx)] = priced
        if priced.ok:
            return None
        return Violation(f"P3_{priced.reason}", "plan", priced.detail)
