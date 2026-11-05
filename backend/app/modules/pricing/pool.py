"""CAR_URBAN_POOL pricing (Revision 9 Sections 13-17; Baseline 2.1-2.4). Pure, exact.

  PlanFare      = BASE + PER_KM x D_plan + PER_MIN x T_plan + STOP_FEE x (k_total_stops - 2)   (13)
  Gate 1        PlanFare <= (1 - d_min) x sum_N P_i                                              (14.1)
  w_i           = P_i (1 + lambda detour_i + mu walk_ratio_i) / (1 + gamma (s_i - 1))            (15.2)
  Cap_i         = P_i (1 - d_min);  EffectiveCap_i = Cap_i, or min(Cap_i, Fare_exact_old(i))     (15.3.2)
  RawFloor_i    = max(BASE, P_i (1 - d_max) (1 + gamma (s_i - 1)));  Floor_i = min(EffCap_i, RawFloor_i)
  allocation    exact breakpoint water-filling on [Floor_i, EffectiveCap_i]  (15.3.4); F1-F3 first
  Fare_charged  = floor(Fare_exact / 1000) x 1000                                                (15.4)
  Gate 2A       (1 - c_pool) sum Fare_charged >= max_N (1 - c_private) P_i                       (14.2)
  Gate 2B       [(1 - c_pool) sum Fare_charged] / (T_plan / 60)
                    >= (1 - eps) max_N [(1 - c_private) P_i / (T_direct(i) / 60)]
  Dynamic insertion: D1-D6 of Section 15.5 (`price_insertion`).

All amounts are `Fraction`s (DD-P3-01): the allocation is solved exactly, so N1
(sum Fare_exact == PlanFare) holds with equality - no 1e-9 tolerance is needed.
Every rejection carries a precise reason code (`REASONS`) and the Section 14 / 15 event name.
"""

from collections.abc import Iterable, Sequence
from dataclasses import dataclass, field
from fractions import Fraction

from app.modules.pricing.money import floor_step, q
from app.modules.pricing.params import CarUrbanParams
from app.modules.pricing.tariff import pool_quote_for

# reason code -> event of Revision 9 (Sections 14.2, 15.3.3, 15.5)
REASONS = {
    "GATE1_PASSENGER_SHAREABILITY": "POOL_SHAREABILITY_REJECTED",
    "GATE2A_DRIVER_PAYOUT": "POOL_SHAREABILITY_REJECTED",
    "GATE2B_DRIVER_HOURLY_RATE": "POOL_SHAREABILITY_REJECTED",
    "INFEASIBLE_UPPER_BOUND": "POOL_ALLOCATION_INFEASIBLE_CAP",
    "INFEASIBLE_LOWER_BOUND": "POOL_ALLOCATION_INFEASIBLE_FLOOR",
    "EMPTY_SET": "POOL_ALLOCATION_INFEASIBLE_CAP",
    "D1_PLAN_NOT_OPEN": "POOL_INSERTION_REJECTED",
    "D1_NO_UNLOCKED_RIDER": "POOL_INSERTION_REJECTED",
    "D1_NO_CO_RIDING_OVERLAP": "POOL_INSERTION_REJECTED",
    "D1_PARTIAL_LOCK_INSERTION_DISABLED": "POOL_INSERTION_REJECTED",
    "D5_OLD_RIDER_PRICE_WOULD_RISE": "POOL_INSERTION_REJECTED",
    "D6_BUDGET_EXCEEDED": "POOL_INSERTION_REJECTED",
    "PLAN_PRICING_STATE_INCONSISTENT": "POOL_INSERTION_REJECTED",
    "INVALID_INPUT": "POOL_INSERTION_REJECTED",
}


# ---- allocation (Section 15.3) ------------------------------------------------

@dataclass(frozen=True)
class Allocation:
    status: str                                   # OK | EMPTY_SET | INFEASIBLE_* (Section 15.3.4)
    fares: dict[str, Fraction] | None = None
    floors_used: dict[str, Fraction] | None = None
    clamped_to_base: bool = False


def _phi(t: Fraction, items: Sequence[tuple[str, Fraction, Fraction, Fraction, Fraction]]) -> Fraction:
    return sum((min(cap, max(floor, p - t * w)) for _, p, w, floor, cap in items), Fraction(0))


def allocate_two_sided(target: Fraction, P: dict[str, Fraction], w: dict[str, Fraction], floor: dict[str, Fraction],
                       cap: dict[str, Fraction]) -> Allocation:
    """AllocateTwoSidedBounded (Section 15.3.4), exact. Keys of P define U."""
    if not P:
        return Allocation("EMPTY_SET")
    items = [(k, P[k], w[k], floor[k], cap[k]) for k in sorted(P)]
    if any(wk <= 0 for _, _, wk, _, _ in items):
        raise ValueError("weights must be > 0")
    if any(fl > cp for _, _, _, fl, cp in items):
        return Allocation("INFEASIBLE_INDIVIDUAL_BOUNDS")   # F1 (excluded by construction of Floor_i)
    sum_floor = sum((fl for _, _, _, fl, _ in items), Fraction(0))
    sum_cap = sum((cp for _, _, _, _, cp in items), Fraction(0))
    if target > sum_cap:
        return Allocation("INFEASIBLE_UPPER_BOUND")          # F3
    if target < sum_floor:
        return Allocation("INFEASIBLE_LOWER_BOUND")          # F2
    if target == sum_cap:
        return Allocation("OK", {k: cp for k, _, _, _, cp in items}, dict(floor))
    if target == sum_floor:
        return Allocation("OK", {k: fl for k, _, _, fl, _ in items}, dict(floor))
    breaks = sorted({(p - cp) / wk for _, p, wk, _, cp in items} | {(p - fl) / wk for _, p, wk, fl, _ in items})
    for a, b in zip(breaks, breaks[1:]):
        fa, fb = _phi(a, items), _phi(b, items)
        if fb <= target <= fa:
            tau = a if fa == fb else a + (fa - target) / (fa - fb) * (b - a)
            fares = {k: min(cp, max(fl, p - tau * wk)) for k, p, wk, fl, cp in items}
            return Allocation("OK", fares, dict(floor))
    raise AssertionError("no breakpoint segment contains the target although F2 and F3 hold")  # pragma: no cover


# ---- riders and bounds ---------------------------------------------------------

@dataclass(frozen=True)
class PoolRider:
    """One booking of a plan as the allocation sees it."""
    ref: str
    private_fare: int              # P_i
    seats: int                     # s_i in {1, 2}
    direct_duration_s: Fraction    # T_direct(i), for gate 2B
    detour: Fraction = Fraction(0)       # (D_actual_in_vehicle - D_direct) / D_direct
    walk_ratio: Fraction = Fraction(0)   # D_walk / D_direct (0: door-to-door)


def seat_factor(p: CarUrbanParams, seats: int) -> Fraction:
    return 1 + p.gamma_seat * (seats - 1)


def weight(p: CarUrbanParams, r: PoolRider) -> Fraction:
    return r.private_fare * (1 + p.lam * r.detour + p.mu * r.walk_ratio) / seat_factor(p, r.seats)


def cap(p: CarUrbanParams, r: PoolRider) -> Fraction:
    return r.private_fare * (1 - p.d_min)


def raw_floor(p: CarUrbanParams, r: PoolRider) -> Fraction:
    return max(Fraction(p.base_vnd), r.private_fare * (1 - p.d_max) * seat_factor(p, r.seats))


def plan_fare(p: CarUrbanParams, d_plan_m: float | Fraction, t_plan_s: float | Fraction, total_stops: int) -> Fraction:
    """Section 13. `total_stops` = every stop of the plan S_0..S_k (extra_stops = k_total_stops - 2)."""
    if total_stops < 2:
        raise ValueError("a plan has at least 2 stops")
    return (p.base_vnd + p.per_km_vnd * q(d_plan_m) / 1000 + p.per_min_vnd * q(t_plan_s) / 60
            + p.stop_fee_vnd * (total_stops - 2))


def gate1(p: CarUrbanParams, fare: Fraction, privates: Iterable[int]) -> bool:
    return fare <= (1 - p.d_min) * sum(privates)


@dataclass(frozen=True)
class Gate2:
    payout: Fraction                # (1 - c_pool) x sum Fare_charged (incl. frozen final prices)
    max_private_payout: Fraction
    hourly: Fraction                # VND / hour
    max_private_hourly: Fraction
    passed_2a: bool
    passed_2b: bool                 # True when the gate is disabled by configuration


def gate2(p: CarUrbanParams, charged_total: int, t_plan_s: Fraction, riders: Iterable[PoolRider]) -> Gate2:
    riders = list(riders)
    payout = (1 - p.commission_pool) * charged_total
    private_payouts = [(1 - p.commission_private) * r.private_fare for r in riders]
    hourly = payout / (t_plan_s / 3600)
    private_hourly = [(1 - p.commission_private) * r.private_fare / (r.direct_duration_s / 3600) for r in riders]
    ok_2a = payout >= max(private_payouts)
    ok_2b = (not p.enforce_hourly_gate) or hourly >= (1 - p.eps_hourly) * max(private_hourly)
    return Gate2(payout, max(private_payouts), hourly, max(private_hourly), ok_2a, ok_2b)


# ---- result -------------------------------------------------------------------------

@dataclass(frozen=True)
class RiderPrice:
    ref: str
    private_fare: int
    seats: int
    group: str                      # NEW | U (re-allocated) | L (frozen)
    quote_cap: Fraction             # Cap_i = P_i (1 - d_min) (G07 bound of a matched booking)
    floor: Fraction | None
    effective_cap: Fraction | None
    weight: Fraction | None
    fare_exact: Fraction
    fare_charged: int
    quote: int
    unmatched: int

    @property
    def rounding_absorbed(self) -> Fraction:
        return self.fare_exact - self.fare_charged


@dataclass(frozen=True)
class PoolPricing:
    status: str                     # OK | REJECTED
    reason: str | None = None
    detail: str = ""
    plan_fare: Fraction | None = None
    target_fare_u: Fraction | None = None
    prices: dict[str, RiderPrice] = field(default_factory=dict)
    gate: Gate2 | None = None
    clamped_to_base: bool = False

    @property
    def ok(self) -> bool:
        return self.status == "OK"

    @property
    def event(self) -> str | None:
        return REASONS.get(self.reason) if self.reason else None


def _reject(reason: str, detail: str = "", **kw: object) -> PoolPricing:
    return PoolPricing("REJECTED", reason, detail, **kw)  # type: ignore[arg-type]


def _check_riders(p: CarUrbanParams, riders: Iterable[PoolRider]) -> str | None:
    for r in riders:
        if r.private_fare <= 0 or r.direct_duration_s <= 0 or not 1 <= r.seats <= p.max_party_seats_pool \
                or r.detour < 0 or r.walk_ratio < 0:
            return f"rider {r.ref}: P_i > 0, T_direct > 0, 1 <= s_i <= {p.max_party_seats_pool}, detour/walk >= 0"
    return None


def _bounds(p: CarUrbanParams, riders: Sequence[PoolRider], caps: dict[str, Fraction]) -> tuple[dict, dict, dict, dict]:
    P = {r.ref: Fraction(r.private_fare) for r in riders}
    w = {r.ref: weight(p, r) for r in riders}
    floor = {r.ref: min(caps[r.ref], raw_floor(p, r)) for r in riders}
    return P, w, floor, caps


def _allocate(p: CarUrbanParams, target: Fraction, P: dict, w: dict, floor: dict, caps: dict) -> Allocation:
    a = allocate_two_sided(target, P, w, floor, caps)
    if a.status == "INFEASIBLE_LOWER_BOUND" and p.on_lower_bound_infeasible == "CLAMP_TO_BASE":
        # Optional mode of Section 15.3.3 ([PROPOSED]); never active unless configured explicitly.
        base_floor = {k: min(caps[k], Fraction(p.base_vnd)) for k in P}
        b = allocate_two_sided(target, P, w, base_floor, caps)
        return Allocation(b.status, b.fares, base_floor, clamped_to_base=b.status == "OK")
    return a


def _charged(p: CarUrbanParams, exact: Fraction) -> int:
    return floor_step(exact, p.step)


# ---- a new plan (Section 15.3, EffectiveCap = Cap) ---------------------------------------

def price_new_plan(p: CarUrbanParams, riders: Sequence[PoolRider], d_plan_m: float | Fraction,
                   t_plan_s: float | Fraction, total_stops: int) -> PoolPricing:
    """Gate 1 -> allocation of the whole plan -> rounding -> gate 2 (Sections 14-15)."""
    if len(riders) < 2 or len({r.ref for r in riders}) != len(riders):
        return _reject("INVALID_INPUT", "a pool plan prices at least two distinct bookings")
    if (bad := _check_riders(p, riders)) is not None:
        return _reject("INVALID_INPUT", bad)
    t_plan = q(t_plan_s)
    if t_plan <= 0:
        return _reject("INVALID_INPUT", "T_plan must be > 0")
    fare = plan_fare(p, d_plan_m, t_plan, total_stops)
    if not gate1(p, fare, (r.private_fare for r in riders)):
        return _reject("GATE1_PASSENGER_SHAREABILITY", f"PlanFare {float(fare):.2f} > (1 - d_min) x sum P_i",
                       plan_fare=fare)
    P, w, floor, caps = _bounds(p, riders, {r.ref: cap(p, r) for r in riders})
    a = _allocate(p, fare, P, w, floor, caps)
    if a.status != "OK":
        return _reject(a.status, plan_fare=fare, target_fare_u=fare)
    prices = {}
    for r in riders:
        exact = a.fares[r.ref]  # type: ignore[index]
        pq = pool_quote_for(p, r.private_fare)
        prices[r.ref] = RiderPrice(r.ref, r.private_fare, r.seats, "U", cap(p, r), a.floors_used[r.ref],  # type: ignore[index]
                                   caps[r.ref], w[r.ref], exact, _charged(p, exact), pq.quote, pq.unmatched)
    g = gate2(p, sum(x.fare_charged for x in prices.values()), t_plan, riders)
    common = dict(plan_fare=fare, target_fare_u=fare, prices=prices, gate=g, clamped_to_base=a.clamped_to_base)
    if not g.passed_2a:
        return _reject("GATE2A_DRIVER_PAYOUT", **common)  # type: ignore[arg-type]
    if not g.passed_2b:
        return _reject("GATE2B_DRIVER_HOURLY_RATE", **common)  # type: ignore[arg-type]
    return PoolPricing("OK", **common)  # type: ignore[arg-type]


# ---- dynamic insertion (Section 15.5, D1-D6) ----------------------------------------------

@dataclass(frozen=True)
class PricedRider:
    """A booking already in the plan, with the outcome of the previous allocation."""
    rider: PoolRider
    locked: bool                          # price_status MATCHED_LOCKED (or already dropped off): group L
    fare_exact_old: Fraction | None       # None: never allocated (the plan had one booking so far)
    fare_charged_old: int | None
    final_price: int | None               # L only: the locked final_price


@dataclass(frozen=True)
class InsertionInput:
    plan_open: bool                       # ride_plan.status == PLAN_OPEN_SEARCHING
    plan_fare_old: Fraction | None        # None while no allocation exists (one booking so far)
    old: Sequence[PricedRider]            # every booking of N_old, including those already dropped off
    new: PoolRider
    new_budget_max: int | None            # B_max(c_new) (None: no budget given)
    co_riding_overlap: bool               # D1: the new rider shares >= 1 segment with a rider of the plan
    d_plan_m: Fraction                    # of the NEW plan, S_0 -> S_k
    t_plan_s: Fraction
    total_stops: int                      # of the new plan, S_0..S_k


def price_insertion(p: CarUrbanParams, x: InsertionInput) -> PoolPricing:
    """D1-D6 of Section 15.5. The frozen group L keeps Fare_exact_old and final_price; only the
    unlocked group U = U_old + {c_new} is re-allocated, each old rider capped by its previous
    Fare_exact (never increased)."""
    if (bad := _check_riders(p, [r.rider for r in x.old] + [x.new])) is not None:
        return _reject("INVALID_INPUT", bad)
    refs = [r.rider.ref for r in x.old] + [x.new.ref]
    if len(set(refs)) != len(refs) or q(x.t_plan_s) <= 0:
        return _reject("INVALID_INPUT", "duplicate rider reference or T_plan <= 0")
    L = [r for r in x.old if r.locked]
    U_old = [r for r in x.old if not r.locked]
    # D1
    if not x.plan_open:
        return _reject("D1_PLAN_NOT_OPEN")
    if not U_old:
        return _reject("D1_NO_UNLOCKED_RIDER")
    if not x.co_riding_overlap:
        return _reject("D1_NO_CO_RIDING_OVERLAP")
    if L and not p.allow_dynamic_insertion_after_partial_lock:
        return _reject("D1_PARTIAL_LOCK_INSERTION_DISABLED")
    # consistency of the stored state of the previous plan version
    allocated = [r.fare_exact_old is not None for r in x.old]
    if any(r.fare_exact_old is None or r.final_price is None for r in L):
        return _reject("PLAN_PRICING_STATE_INCONSISTENT", "a locked rider has no frozen Fare_exact / final_price")
    if any(allocated) and not all(allocated):
        return _reject("PLAN_PRICING_STATE_INCONSISTENT", "some riders were allocated, others not")
    first_match = not any(allocated)
    if first_match and len(x.old) > 1:
        # once two bookings share a plan an allocation exists (it was accepted with the second one)
        return _reject("PLAN_PRICING_STATE_INCONSISTENT", "several bookings in the plan but no allocation")
    if not first_match:
        if x.plan_fare_old is None or sum(r.fare_exact_old for r in x.old) != x.plan_fare_old:  # type: ignore[misc]
            return _reject("PLAN_PRICING_STATE_INCONSISTENT", "sum Fare_exact_old != PlanFare_old")
        if any(r.fare_charged_old is None for r in U_old):
            return _reject("PLAN_PRICING_STATE_INCONSISTENT", "an unlocked rider has no Fare_charged_old")

    t_plan = q(x.t_plan_s)
    fare_new = plan_fare(p, x.d_plan_m, t_plan, x.total_stops)
    everyone = [r.rider for r in x.old] + [x.new]
    # D2: frozen L, dynamic caps on U
    frozen = sum((r.fare_exact_old for r in L), Fraction(0))  # type: ignore[misc]
    target = fare_new - frozen
    U = [r.rider for r in U_old] + [x.new]
    caps = {r.rider.ref: cap(p, r.rider) if first_match else min(cap(p, r.rider), r.fare_exact_old)  # type: ignore[type-var]
            for r in U_old} | {x.new.ref: cap(p, x.new)}
    P, w, floor, caps = _bounds(p, U, caps)
    # Gate 1 on the whole new plan (D5 lists it; it is checked first because it needs no allocation)
    if not gate1(p, fare_new, (r.private_fare for r in everyone)):
        return _reject("GATE1_PASSENGER_SHAREABILITY", plan_fare=fare_new, target_fare_u=target)
    # D3 / D4 (F3 / F2 on U) and the allocation of D5
    a = _allocate(p, target, P, w, floor, caps)
    if a.status != "OK":
        return _reject(a.status, plan_fare=fare_new, target_fare_u=target)
    prices: dict[str, RiderPrice] = {}
    for r in L:
        pq = pool_quote_for(p, r.rider.private_fare)
        prices[r.rider.ref] = RiderPrice(r.rider.ref, r.rider.private_fare, r.rider.seats, "L", cap(p, r.rider),
                                         None, None, None,
                                         r.fare_exact_old, r.final_price, pq.quote, pq.unmatched)  # type: ignore[arg-type]
    for r in U:
        exact = a.fares[r.ref]  # type: ignore[index]
        pq = pool_quote_for(p, r.private_fare)
        prices[r.ref] = RiderPrice(r.ref, r.private_fare, r.seats, "NEW" if r.ref == x.new.ref else "U", cap(p, r),
                                   a.floors_used[r.ref], caps[r.ref], w[r.ref], exact,  # type: ignore[index]
                                   _charged(p, exact), pq.quote, pq.unmatched)
    # D5: no unlocked old rider pays more, before or after rounding
    if not first_match:
        for r in U_old:
            new_price = prices[r.rider.ref]
            if new_price.fare_exact > r.fare_exact_old or new_price.fare_charged > r.fare_charged_old:  # type: ignore[operator]
                return _reject("D5_OLD_RIDER_PRICE_WOULD_RISE", r.rider.ref, plan_fare=fare_new, target_fare_u=target,
                               prices=prices)
    # D5: gate 2 on the whole plan after rounding (L counts with its final_price)
    charged_total = sum(x_.fare_charged for x_ in prices.values())
    g = gate2(p, charged_total, t_plan, everyone)
    common = dict(plan_fare=fare_new, target_fare_u=target, prices=prices, gate=g, clamped_to_base=a.clamped_to_base)
    if not g.passed_2a:
        return _reject("GATE2A_DRIVER_PAYOUT", **common)  # type: ignore[arg-type]
    if not g.passed_2b:
        return _reject("GATE2B_DRIVER_HOURLY_RATE", **common)  # type: ignore[arg-type]
    # D6: budget of the new rider
    new_unmatched = prices[x.new.ref].unmatched
    if x.new_budget_max is not None and new_unmatched > x.new_budget_max:
        return _reject("D6_BUDGET_EXCEEDED", f"Unmatched {new_unmatched} > B_max {x.new_budget_max}", **common)  # type: ignore[arg-type]
    return PoolPricing("OK", **common)  # type: ignore[arg-type]


# ---- final price at pool_lock_point (Section 11, 18.5) ------------------------------------

def final_price_at_lock(p: CarUrbanParams, private: int, matched: bool, fare_charged: int | None,
                        unmatched_cause: str) -> int:
    """MATCHED_LOCKED: the current Fare_charged (<= Quote_i). UNMATCHED_LOCKED: Unmatched_i, or Quote_i
    when the cause is DRIVER_DECLINED (Section 11, table 18.5). The state transition itself is Phase 4."""
    pq = pool_quote_for(p, private)
    if matched:
        if fare_charged is None or fare_charged > pq.quote:
            raise ValueError("a matched booking locks a Fare_charged <= Quote_i")
        return fare_charged
    return pq.quote if unmatched_cause == "DRIVER_DECLINED" else pq.unmatched
