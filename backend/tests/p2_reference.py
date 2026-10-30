"""Independent reference for the P2 tests: re-derives every hard constraint of Revision 9
Section 7 for a finished stop chain straight from the matrices, without the production
`simulate` / `evaluate_chain` / `check_all`. Used as the "0 violations" measure and as a
brute-force optimum for the Section 36 insertion."""

import itertools
from datetime import datetime, timedelta

from app.modules.candidate.constraints import KYC_REQUIRED, VEHICLE_FOR
from app.modules.pooling.insertion import PICKUP, PlanState, RiderSpec, Stop


def violations(state: PlanState, chain: tuple[Stop, ...], riders: dict[str, RiderSpec], D, T,  # noqa: ANN001
               service: str, source: str, dwell_s: float, k_max: int, stale_s: float,
               booking_ok: bool = True) -> set[str]:
    bad: set[str] = set()
    d = state.driver
    # 1
    if d.availability == "OFFLINE" or d.location_age_s > stale_s or (source == "NEW_SINGLE_VEHICLE" and d.availability != "IDLE"):
        bad.add("HC01")
    if d.vehicle_id is None or not d.vehicle_active or d.vehicle_type != VEHICLE_FOR[service]:
        bad.add("HC01")
    if not d.accepts_urban or (service == "CAR_URBAN_POOL" and not d.pool_enabled):
        bad.add("HC01")
    if service in KYC_REQUIRED and d.kyc_status != "VERIFIED":
        bad.add("HC01")
    # walk the chain
    clock, dist, node = 0.0, 0.0, state.current_node
    at: dict[tuple[str, str], tuple[float, float]] = {}
    seats = sum(r.seats for r in riders.values() if r.onboard)
    aboard = {ref for ref, r in riders.items() if r.onboard}
    overlaps: set[frozenset[str]] = {frozenset(p) for p in itertools.combinations(sorted(aboard), 2)}
    for stop in chain:
        if D[node][stop.node] is None or T[node][stop.node] is None:
            bad.add("HC02")
            leg_d = leg_t = 0.0
        else:
            leg_d, leg_t = D[node][stop.node], T[node][stop.node]
        if seats > d.capacity:
            bad.add("HC04")
        clock += leg_t
        dist += leg_d
        r = riders[stop.ref]
        if stop.kind == PICKUP:
            earliest = (r.pickup_window[0] - state.now).total_seconds()
            clock = max(clock, earliest)
            seats += r.seats
            for other in aboard:
                overlaps.add(frozenset((other, stop.ref)))
            aboard.add(stop.ref)
        else:
            seats -= r.seats
            aboard.discard(stop.ref)
        at[(stop.ref, stop.kind)] = (clock, dist)
        clock += dwell_s
        node = stop.node
    for ref, r in riders.items():
        t_drop, d_drop = at[(ref, "DROPOFF")]
        if r.onboard:
            ride = r.traveled_m + d_drop
            in_vehicle = (state.now - r.actual_pickup).total_seconds() + t_drop
        else:
            t_pick, d_pick = at[(ref, PICKUP)]
            lo, hi = r.pickup_window
            pick_at = state.now + timedelta(seconds=t_pick)
            if not lo <= pick_at <= hi:
                bad.add("HC03")
            ride = d_drop - d_pick
            in_vehicle = t_drop - t_pick
        if service == "CAR_URBAN_POOL" and r.direct_distance_m > 0 and (ride - r.direct_distance_m) / r.direct_distance_m > r.max_detour_ratio + 1e-9:
            bad.add("HC05")
        if in_vehicle > r.max_in_vehicle_s + 1e-6:
            bad.add("HC06")
        if r.latest_arrival is not None and state.now + timedelta(seconds=t_drop) > r.latest_arrival:
            bad.add("HC06")
        if r.budget_max_vnd is not None and (r.max_price_vnd is None or r.max_price_vnd > r.budget_max_vnd):
            bad.add("HC08")
        if r.walk_m > r.max_walk_m:
            bad.add("HC10")
    if service == "CAR_URBAN_POOL":
        if state.completed_stops + len(chain) > k_max or len(riders) - 1 > d.max_additional_pickups:
            bad.add("HC07")
        if source == "EXISTING_POOL_PLAN":
            old_m, old_s = _length(state, D, T, riders, dwell_s)
            new_m, new_s = dist, clock
            if d.max_driver_detour_km is not None and new_m - old_m > d.max_driver_detour_km * 1000 + 1e-6:
                bad.add("HC07")
            if d.max_driver_detour_min is not None and new_s - old_s > d.max_driver_detour_min * 60 + 1e-6:
                bad.add("HC07")
    for pair in overlaps:
        a, b = (riders[x] for x in pair)
        if (a.same_gender or b.same_gender) and (a.verified_gender is None or a.verified_gender != b.verified_gender):
            bad.add("HC11")
    if not booking_ok:
        bad.add("HC09")
    return bad


def _length(state: PlanState, D, T, riders: dict[str, RiderSpec], dwell_s: float) -> tuple[float, float]:  # noqa: ANN001
    clock = dist = 0.0
    node = state.current_node
    for stop in state.remaining:
        clock += T[node][stop.node] or 0.0
        dist += D[node][stop.node] or 0.0
        if stop.kind == PICKUP:
            clock = max(clock, (riders[stop.ref].pickup_window[0] - state.now).total_seconds())
        clock += dwell_s
        node = stop.node
    return dist, clock


def brute_force(state: PlanState, new: RiderSpec, p_node: int, q_node: int, D, T, service: str, source: str,  # noqa: ANN001
                dwell_s: float, k_max: int, stale_s: float, per_km: float, per_min: float) -> float | None:
    """Cheapest feasible insertion by enumerating every (P, Q) position pair."""
    riders = {r.ref: r for r in state.riders} | {new.ref: new}
    rem = list(state.remaining)
    best = None
    old_m, old_s = _length(state, D, T, riders, dwell_s) if rem else (0.0, 0.0)
    for i, j in itertools.combinations_with_replacement(range(len(rem) + 1), 2):
        chain = (*rem[:i], Stop(p_node, PICKUP, new.ref), *rem[i:j], Stop(q_node, "DROPOFF", new.ref), *rem[j:])
        if violations(state, chain, riders, D, T, service, source, dwell_s, k_max, stale_s):
            continue
        clock = dist = 0.0
        node = state.current_node
        for stop in chain:
            clock += T[node][stop.node]
            dist += D[node][stop.node]
            if stop.kind == PICKUP:
                clock = max(clock, (riders[stop.ref].pickup_window[0] - state.now).total_seconds())
            clock += dwell_s
            node = stop.node
        cost = per_km * (dist - old_m) / 1000 + per_min * (clock - old_s) / 60
        best = cost if best is None or cost < best else best
    return best


def at(now: datetime, seconds: float) -> datetime:
    return now + timedelta(seconds=seconds)
