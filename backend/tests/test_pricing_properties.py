"""P3 - the property-based invariants of Revision 9 Section 71.2 on at least 10.000 generated
inputs (2-4 bookings, 2-30 km, s_i in {1, 2}, detour 0..0.30, walk 0..0.20), plus the dynamic
insertion invariants of gate G08.

Every example is checked against an INDEPENDENT exact solver (`reference_allocation`: active-set
enumeration - each rider at Floor, at Cap or free, 3^n cases - not the breakpoint algorithm of
pricing.pool). The run is deterministic (`derandomize=True`) and counts its examples: the test
fails if fewer than 10.000 were checked, so "the run finished" is never mistaken for "the
invariants hold".

Invariant 1 is checked with equality (exact rationals), stronger than the |difference| < 1e-6 of
71.2. Invariant 5 compares bookings with the same seat count (SF-P3-03)."""

import itertools
from fractions import Fraction

import yaml
from hypothesis import HealthCheck, given, settings
from hypothesis import strategies as st

from app.modules.pricing import pool, settlement, tariff
from app.modules.pricing.money import floor_step
from app.modules.pricing.params import PricingParams
from tests.conftest import CONFIG_BASELINE

BASELINE = yaml.safe_load(CONFIG_BASELINE.read_text(encoding="utf-8"))
PARAMS = PricingParams.from_sections(BASELINE["pricing_version"], BASELINE["pool_policy_version"], BASELINE)
CAR = PARAMS.car
EXAMPLES = 10_000
STATS = {"examples": 0, "allocated": 0, "infeasible_low": 0, "infeasible_high": 0, "plans_accepted": 0,
         "insertions_accepted": 0, "insertions_with_lock": 0}


def reference_allocation(target: Fraction, P: dict, w: dict, lo: dict, hi: dict) -> dict | None:
    """Independent exact solver of sum f_i = target, f_i = clamp(P_i - tau w_i, lo_i, hi_i)."""
    if not lo or not sum(lo.values()) <= target <= sum(hi.values()):
        return None
    keys = sorted(P)
    for states in itertools.product(("lo", "hi", "free"), repeat=len(keys)):
        fixed = sum((lo[k] if s == "lo" else hi[k] for k, s in zip(keys, states) if s != "free"), Fraction(0))
        free = [k for k, s in zip(keys, states) if s == "free"]
        if not free:
            if fixed != target:
                continue
            # every rider clamped: valid only if ONE tau puts each at its bound
            # (at lo: P - tau w <= lo  <=>  tau >= (P - lo) / w; at hi: tau <= (P - hi) / w)
            need = [(P[k] - lo[k]) / w[k] for k, s in zip(keys, states) if s == "lo"]
            allow = [(P[k] - hi[k]) / w[k] for k, s in zip(keys, states) if s == "hi"]
            if need and allow and max(need) > min(allow):
                continue
            return {k: lo[k] if s == "lo" else hi[k] for k, s in zip(keys, states)}
        tau = (sum(P[k] for k in free) - (target - fixed)) / sum(w[k] for k in free)
        fares = {}
        ok = True
        for k, s in zip(keys, states):
            v = P[k] - tau * w[k]
            if s == "free":
                ok &= lo[k] <= v <= hi[k]
                fares[k] = v
            elif s == "lo":
                ok &= v <= lo[k]
                fares[k] = lo[k]
            else:
                ok &= v >= hi[k]
                fares[k] = hi[k]
            if not ok:
                break
        if ok:
            return fares
    raise AssertionError("no active set found although the problem is feasible")


@st.composite
def rider(draw: st.DrawFn, ref: str) -> pool.PoolRider:
    km_m = draw(st.integers(2000, 30000))
    min_per_km = Fraction(draw(st.integers(150, 400)), 100)           # 1,5 - 4 min / km
    t_s = Fraction(km_m, 1000) * min_per_km * 60
    P = tariff.private_fare(CAR, km_m, t_s)
    return pool.PoolRider(ref, P, draw(st.sampled_from((1, 2))), t_s, Fraction(draw(st.integers(0, 300)), 1000),
                          Fraction(draw(st.integers(0, 200)), 1000))


@st.composite
def scenario(draw: st.DrawFn) -> tuple[list[pool.PoolRider], Fraction, int, int, Fraction]:
    n = draw(st.integers(2, 4))
    riders = [draw(rider(f"r{i}")) for i in range(n)]
    u = Fraction(draw(st.integers(-150, 1150)), 1000)                   # position of PlanFare in [sum Floor, sum Cap]
    bump_i = draw(st.integers(0, n - 1))
    bump = Fraction(draw(st.integers(1, 200)), 1000)
    swap_j = draw(st.integers(0, n - 1))
    t_plan = Fraction(draw(st.integers(10 * 60, 120 * 60)))
    return riders, u, bump_i, swap_j, bump, t_plan  # type: ignore[return-value]


def bounds(riders: list[pool.PoolRider]) -> tuple[dict, dict, dict, dict]:
    caps = {r.ref: pool.cap(CAR, r) for r in riders}
    return pool._bounds(CAR, riders, caps)


def check_allocation(riders: list[pool.PoolRider], u: Fraction, bump_i: int, swap_j: int, bump: Fraction) -> None:
    P, w, lo, hi = bounds(riders)
    target = sum(lo.values()) + u * (sum(hi.values()) - sum(lo.values()))
    a = pool.allocate_two_sided(target, P, w, lo, hi)
    ref = reference_allocation(target, P, w, lo, hi)
    if target > sum(hi.values()):
        assert a.status == "INFEASIBLE_UPPER_BOUND" and ref is None
        STATS["infeasible_high"] += 1
        return
    if target < sum(lo.values()):
        assert a.status == "INFEASIBLE_LOWER_BOUND" and ref is None
        STATS["infeasible_low"] += 1
        return
    STATS["allocated"] += 1
    assert a.status == "OK" and a.fares == ref                                              # independent solver
    assert sum(a.fares.values()) == target                                                  # invariant 1 (exact)
    for r in riders:
        exact = a.fares[r.ref]
        assert lo[r.ref] <= exact <= hi[r.ref]                                             # invariant 2 / G06 / G07
        charged = floor_step(exact, 1000)
        pq = tariff.pool_quote_for(CAR, r.private_fare)
        assert 0 < charged <= pq.quote < pq.unmatched < r.private_fare                    # invariant 3
        s = settlement.settle_pool_matched(PARAMS, charged)                                 # invariant 7
        assert s.driver_base + s.platform_net + s.fund_contribution == charged
        u_s = settlement.settle_pool_unmatched(PARAMS, r.private_fare, pq.unmatched, "NO_COMPATIBLE")  # invariant 6
        assert u_s.driver_base + u_s.guarantee == r.private_fare * Fraction(4, 5)
    # invariant 4: more detour (or walk) for rider i, same PlanFare and P_j -> Fare_exact(i) does not rise
    i = riders[bump_i]
    more = [pool.PoolRider(r.ref, r.private_fare, r.seats, r.direct_duration_s, r.detour + bump, r.walk_ratio)
            if r is i else r for r in riders]
    P2, w2, lo2, hi2 = bounds(more)
    b = pool.allocate_two_sided(target, P2, w2, lo2, hi2)
    assert b.status == "OK" and b.fares[i.ref] <= a.fares[i.ref]
    walk = [pool.PoolRider(r.ref, r.private_fare, r.seats, r.direct_duration_s, r.detour, r.walk_ratio + bump)
            if r is i else r for r in riders]
    c = pool.allocate_two_sided(target, *bounds(walk))
    assert c.status == "OK" and c.fares[i.ref] <= a.fares[i.ref]
    # invariant 5: same detour, walk and seats, larger P -> pays at least as much
    j = riders[swap_j]
    if j is not i:
        same = [pool.PoolRider(r.ref, r.private_fare, i.seats, r.direct_duration_s, i.detour, i.walk_ratio)
                if r is j else r for r in riders]
        Ps, ws, los, his = bounds(same)
        t2 = sum(los.values()) + u * (sum(his.values()) - sum(los.values()))
        d = pool.allocate_two_sided(t2, Ps, ws, los, his)
        if d.status == "OK":
            hi_ref, lo_ref = (i.ref, j.ref) if i.private_fare >= j.private_fare else (j.ref, i.ref)
            if Ps[hi_ref] > Ps[lo_ref]:
                assert d.fares[hi_ref] >= d.fares[lo_ref]


def check_plan_and_insertion(riders: list[pool.PoolRider], u: Fraction, t_plan: Fraction) -> None:
    """Whole pipeline (gate 1, allocation, rounding, gate 2) and a dynamic insertion on top of it."""
    old, new = riders[:-1], riders[-1]
    if len(old) < 2:
        return
    P, w, lo, hi = bounds(old)
    fare = sum(lo.values()) + max(Fraction(0), min(Fraction(1), u)) * (sum(hi.values()) - sum(lo.values()))
    stops = 2 * len(old)
    d_m = (fare - CAR.base_vnd - CAR.per_min_vnd * t_plan / 60 - CAR.stop_fee_vnd * (stops - 2)) / CAR.per_km_vnd * 1000
    if d_m <= 0:
        return
    res = pool.price_new_plan(CAR, old, d_m, t_plan, stops)
    if not res.ok:
        if res.reason in ("GATE2A_DRIVER_PAYOUT", "GATE2B_DRIVER_HOURLY_RATE"):
            assert res.gate is not None and not (res.gate.passed_2a and res.gate.passed_2b)
        return
    STATS["plans_accepted"] += 1
    g = res.gate
    assert g.payout >= g.max_private_payout and g.hourly >= g.max_private_hourly                  # invariant 6, G09
    assert g.payout == Fraction(85, 100) * sum(x.fare_charged for x in res.prices.values())
    assert sum(x.fare_exact for x in res.prices.values()) == res.plan_fare                        # N1
    assert sum(x.fare_charged + x.rounding_absorbed for x in res.prices.values()) == res.plan_fare  # 17.2
    # dynamic insertion: lock the first rider, add `new`, PlanFare grows by a share of Cap_new
    locked_ref = old[0].ref
    priced = [pool.PricedRider(r, r.ref == locked_ref, res.prices[r.ref].fare_exact, res.prices[r.ref].fare_charged,
                               res.prices[r.ref].fare_charged if r.ref == locked_ref else None) for r in old]
    delta = pool.cap(CAR, new) * u if u > 0 else pool.cap(CAR, new) / 2
    fare_new = res.plan_fare + delta
    t_new = t_plan + new.direct_duration_s / 4
    d_new = (fare_new - CAR.base_vnd - CAR.per_min_vnd * t_new / 60 - CAR.stop_fee_vnd * (stops)) / CAR.per_km_vnd * 1000
    if d_new <= 0:
        return
    x = pool.InsertionInput(True, res.plan_fare, priced, new, None, True, d_new, t_new, stops + 2)
    ins = pool.price_insertion(CAR, x)
    if not ins.ok:
        return
    STATS["insertions_accepted"] += 1
    STATS["insertions_with_lock"] += 1
    assert sum(p.fare_exact for p in ins.prices.values()) == fare_new                             # N1 after insertion
    for r in old:                                                                                 # G08
        before, after = res.prices[r.ref], ins.prices[r.ref]
        if r.ref == locked_ref:
            assert (after.fare_exact, after.fare_charged, after.group) == (before.fare_exact, before.fare_charged, "L")
        else:
            assert after.fare_exact <= before.fare_exact and after.fare_charged <= before.fare_charged
            assert after.floor <= after.fare_exact <= after.effective_cap
    nx = ins.prices[new.ref]
    assert nx.floor <= nx.fare_exact <= pool.cap(CAR, new) and nx.fare_charged <= nx.quote          # G06, G07
    assert ins.gate.payout >= ins.gate.max_private_payout and ins.gate.hourly >= ins.gate.max_private_hourly


@settings(max_examples=EXAMPLES, derandomize=True, deadline=None, database=None,
          suppress_health_check=[HealthCheck.too_slow, HealthCheck.data_too_large])
@given(scenario())
def _invariants(case: tuple) -> None:
    riders, u, bump_i, swap_j, bump, t_plan = case
    STATS["examples"] += 1
    check_allocation(riders, u, bump_i, swap_j, bump)
    check_plan_and_insertion(riders, u, t_plan)


def test_section_71_2_invariants_on_10000_examples() -> None:
    for k in STATS:
        STATS[k] = 0
    _invariants()
    assert STATS["examples"] >= EXAMPLES, STATS
    # the generator must actually exercise every branch, not only the easy one
    assert STATS["allocated"] > 0.6 * EXAMPLES, STATS
    assert STATS["infeasible_low"] > 100 and STATS["infeasible_high"] > 100, STATS
    assert STATS["plans_accepted"] > 500 and STATS["insertions_accepted"] > 100, STATS
    print("71.2 property run:", STATS)
