"""Dynamic pickup / dropoff insertion aware of the running vehicle (Revision 9 Section 36,
[ACCEPTED] P1-01).

Pure: works on one OSRM table (D in metres, T in seconds) indexed by node, built by the
caller with ONE matrix request (Section 34, P2-04) - no routing call happens here.

  F = [S_curr, S_{r+1}, ..., S_k]: only stops AHEAD of the vehicle are candidates; the
  completed stops S_0..S_r are frozen and S_curr is the vehicle's current position.
  For p_idx in 0..m_f-1, q_idx in p_idx..m_f-1: P goes right after F[p_idx], Q right
  after F[q_idx] (and after P). Each option is simulated with table look-ups plus the
  dwell time at every stop, then:
    step 1  k_max_stops and max_additional_pickups (hard constraint 7)
    step 2  seat load of every segment (hard constraint 4)
    step 3  all 11 hard constraints for EVERY rider of the plan (candidate.constraints)
    step 4-5 pricing feasibility (PlanFare, gate 1, D1-D6, allocation, gate 2) - Phase 3,
            through the optional `pricing_check`; without it the result is PENDING_P3
    step 6  keep the option with the smallest incremental cost.

A vehicle that reaches a pickup before T_earliest waits there (planned pickup =
T_earliest). The incremental cost is PlanFare_new - PlanFare_old with PlanFare of
Section 13 (BASE cancels; PER_KM x extra distance + PER_MIN x extra elapsed time +
STOP_FEE x 2 new stops).

A new single vehicle (Section 35.1) and a new pool plan from an idle driver (Section
35.2 branch B) are the same computation on an empty plan: chain [P, Q].
"""

import uuid
from collections import Counter
from collections.abc import Callable, Sequence
from dataclasses import dataclass, field, replace
from datetime import datetime, timedelta

from app.modules.candidate.constraints import (
    EXISTING_POOL_PLAN,
    DriverState,
    Evaluation,
    RiderOutcome,
    Violation,
    check_all,
)

PICKUP, DROPOFF = "PICKUP", "DROPOFF"
Cell = float | None


@dataclass(frozen=True)
class Stop:
    node: int        # index into the matrix
    kind: str        # PICKUP | DROPOFF
    ref: str         # rider reference


@dataclass(frozen=True)
class RiderSpec:
    ref: str
    seats: int
    onboard: bool
    pickup_window: tuple[datetime, datetime] | None    # None when onboard
    actual_pickup: datetime | None                     # onboard only
    traveled_m: float                                  # onboard only: distance since boarding
    direct_distance_m: float
    direct_duration_s: float
    max_detour_ratio: float
    max_in_vehicle_s: float
    latest_arrival: datetime | None
    max_price_vnd: int | None
    budget_max_vnd: int | None
    walk_m: int = 0
    max_walk_m: int = 0
    same_gender: bool = False
    verified_gender: str | None = None


@dataclass(frozen=True)
class PlanState:
    plan_id: uuid.UUID | None          # None for a new vehicle / new plan
    plan_version: int | None
    driver: DriverState
    current_node: int                  # S_curr (or the idle driver's position)
    now: datetime
    completed_stops: int               # r + 1
    remaining: tuple[Stop, ...]        # S_{r+1} .. S_k
    riders: tuple[RiderSpec, ...]      # every booking of the plan (onboard or waiting)


@dataclass(frozen=True)
class Params:
    dwell_s: float
    k_max_stops: int
    location_stale_s: float
    per_km_vnd: float
    per_min_vnd: float
    stop_fee_vnd: float


@dataclass(frozen=True)
class Simulation:
    events_s: tuple[float, ...]       # pickup boarding / dropoff arrival, seconds after `now`
    cum_m: tuple[float, ...]          # distance driven when reaching each stop
    total_m: float
    elapsed_s: float                  # until the last stop is served (incl. waits and dwell)
    unroutable: tuple[str, ...]


@dataclass(frozen=True)
class InsertionResult:
    p_idx: int
    q_idx: int
    chain: tuple[Stop, ...]
    evaluation: Evaluation
    added_distance_m: float
    added_duration_s: float
    delta_cost_vnd: float
    pricing_check: str                # COMPLETE | PENDING_P3


@dataclass
class InsertionReport:
    best: InsertionResult | None
    options_tried: int = 0
    rejections: Counter = field(default_factory=Counter)   # hard-constraint code -> options rejected


PricingCheck = Callable[[InsertionResult], Violation | None]


def simulate(chain: Sequence[Stop], start: int, D: Sequence[Sequence[Cell]], T: Sequence[Sequence[Cell]],
             windows: dict[str, float], dwell_s: float) -> Simulation:
    """windows: rider ref -> earliest pickup (seconds after now) for riders not yet onboard."""
    t = dist = 0.0
    node = start
    events, cum, unroutable = [], [], []
    for stop in chain:
        leg_d, leg_t = D[node][stop.node], T[node][stop.node]
        if leg_d is None or leg_t is None:
            unroutable.append(f"{node}->{stop.node}")
            leg_d, leg_t = 0.0, 0.0
        t += leg_t
        dist += leg_d
        if stop.kind == PICKUP and t < windows.get(stop.ref, t):
            t = windows[stop.ref]
        events.append(t)
        cum.append(dist)
        t += dwell_s
        node = stop.node
    return Simulation(tuple(events), tuple(cum), dist, t, tuple(unroutable))


def _loads(chain: Sequence[Stop], riders: dict[str, RiderSpec]) -> tuple[int, ...]:
    load = sum(r.seats for r in riders.values() if r.onboard)
    loads = []
    for stop in chain:
        loads.append(load)  # segment ending at this stop
        load += riders[stop.ref].seats if stop.kind == PICKUP else -riders[stop.ref].seats
    return tuple(loads)


def evaluate_chain(state: PlanState, chain: Sequence[Stop], riders: dict[str, RiderSpec], sim: Simulation,
                   service_code: str, source_type: str, booking_time: tuple[bool, str], params: Params,
                   base: Simulation | None) -> Evaluation:
    now = state.now
    index = {(s.ref, s.kind): i for i, s in enumerate(chain)}
    outcomes = []
    for ref, r in riders.items():
        q = index[(ref, DROPOFF)]
        dropoff_s = sim.events_s[q]
        if r.onboard:
            p, pickup_at = -1, None
            ride_m = r.traveled_m + sim.cum_m[q]
            in_vehicle = (now - r.actual_pickup).total_seconds() + dropoff_s  # type: ignore[operator]
        else:
            p = index[(ref, PICKUP)]
            pickup_at = now + timedelta(seconds=sim.events_s[p])
            ride_m = sim.cum_m[q] - sim.cum_m[p]
            in_vehicle = dropoff_s - sim.events_s[p]
        outcomes.append(RiderOutcome(
            ref=ref, seats=r.seats, onboard=r.onboard, span=(p + 1, q + 1), pickup_window=r.pickup_window,
            planned_pickup=pickup_at, planned_dropoff=now + timedelta(seconds=dropoff_s), in_vehicle_s=in_vehicle,
            max_in_vehicle_s=r.max_in_vehicle_s, ride_distance_m=ride_m, direct_distance_m=r.direct_distance_m,
            max_detour_ratio=r.max_detour_ratio, latest_arrival=r.latest_arrival, max_price_vnd=r.max_price_vnd,
            budget_max_vnd=r.budget_max_vnd, walk_m=r.walk_m, max_walk_m=r.max_walk_m, same_gender=r.same_gender,
            verified_gender=r.verified_gender))
    # Driver detour (constraint 7) is the growth of an EXISTING plan; a new vehicle has none.
    existing = source_type == EXISTING_POOL_PLAN
    added_m = sim.total_m - (base.total_m if base else 0.0) if existing else 0.0
    added_s = sim.elapsed_s - (base.elapsed_s if base else 0.0) if existing else 0.0
    return Evaluation(
        service_code=service_code, source_type=source_type, driver=state.driver,
        location_stale_s=params.location_stale_s, unroutable_legs=sim.unroutable,
        segment_loads=_loads(chain, riders), riders=tuple(outcomes),
        booking_time_ok=booking_time[0], booking_time_detail=booking_time[1],
        added_distance_m=added_m, added_duration_s=added_s,
        added_pickups=max(0, len(riders) - 1), total_stops=state.completed_stops + len(chain),
        k_max_stops=params.k_max_stops)


def insert(state: PlanState, new: RiderSpec, p_node: int, q_node: int, D: Sequence[Sequence[Cell]],
           T: Sequence[Sequence[Cell]], service_code: str, source_type: str, booking_time: tuple[bool, str],
           params: Params, pricing_check: PricingCheck | None = None) -> InsertionReport:
    riders = {r.ref: r for r in state.riders} | {new.ref: new}
    now = state.now
    windows = {ref: (r.pickup_window[0] - now).total_seconds() for ref, r in riders.items()
               if not r.onboard and r.pickup_window is not None}
    report = InsertionReport(best=None)
    remaining = list(state.remaining)
    base = simulate(remaining, state.current_node, D, T, windows, params.dwell_s) if remaining else None
    m_f = len(remaining) + 1
    driver = state.driver
    # Step 1 does not depend on the position: evaluated once, reported per option.
    stops_after = state.completed_stops + len(remaining) + 2
    extra_pickups = len(riders) - 1
    step1 = [code for code, bad in (("HC07", stops_after > params.k_max_stops),
                                    ("HC07", extra_pickups > driver.max_additional_pickups
                                     and source_type == EXISTING_POOL_PLAN)) if bad]
    p_stop, q_stop = Stop(p_node, PICKUP, new.ref), Stop(q_node, DROPOFF, new.ref)
    for p_idx in range(m_f):
        for q_idx in range(p_idx, m_f):
            report.options_tried += 1
            if step1:
                report.rejections["HC07"] += 1
                continue
            chain = (*remaining[:p_idx], p_stop, *remaining[p_idx:q_idx], q_stop, *remaining[q_idx:])
            loads = _loads(chain, riders)
            if any(load > driver.capacity for load in loads):
                report.rejections["HC04"] += 1
                continue
            sim = simulate(chain, state.current_node, D, T, windows, params.dwell_s)
            ev = evaluate_chain(state, chain, riders, sim, service_code, source_type, booking_time, params, base)
            violations = check_all(ev)
            if violations:
                for code in {v.code for v in violations}:
                    report.rejections[code] += 1
                continue
            extra_m = sim.total_m - (base.total_m if base else 0.0)
            extra_s = sim.elapsed_s - (base.elapsed_s if base else 0.0)
            delta = params.per_km_vnd * extra_m / 1000 + params.per_min_vnd * extra_s / 60 + params.stop_fee_vnd * 2
            result = InsertionResult(p_idx=p_idx, q_idx=q_idx, chain=chain, evaluation=ev, added_distance_m=extra_m,
                                     added_duration_s=extra_s, delta_cost_vnd=delta, pricing_check="PENDING_P3")
            if pricing_check is not None:
                rejected = pricing_check(result)
                if rejected is not None:
                    report.rejections[rejected.code] += 1
                    continue
                result = replace(result, pricing_check="COMPLETE")
            if report.best is None or delta < report.best.delta_cost_vnd:
                report.best = result
    return report
