"""P3.2 - P3.4 unit tests: allocation boundaries (Floor_i / Cap_i, both bounds at once, F1-F3),
gate 1 / gate 2 boundaries, D1-D6 one by one, the frozen group L, multi-seat bookings, and the
validation of the pricing parameters. Exact arithmetic: equalities, not tolerances."""

from dataclasses import replace
from fractions import Fraction

import pytest
import yaml

from app.modules.pricing import pool, tariff
from app.modules.pricing.money import NonIntegralAmount, exact_vnd, floor_step, from_rational_text, q, to_numeric_2, \
    to_rational_text
from app.modules.pricing.params import CarUrbanParams, PricingConfigError, PricingParams
from tests.conftest import CONFIG_BASELINE

BASELINE = yaml.safe_load(CONFIG_BASELINE.read_text(encoding="utf-8"))


@pytest.fixture(scope="module")
def car() -> CarUrbanParams:
    return CarUrbanParams.from_section(BASELINE["car_urban"])


def R(ref: str, P: int, t_min: float = 30, detour: str = "0", seats: int = 1, walk: str = "0") -> pool.PoolRider:
    return pool.PoolRider(ref, P, seats, q(t_min) * 60, q(detour), q(walk))


# ---- money -----------------------------------------------------------------------------

def test_money_is_exact() -> None:
    assert q(0.85) == Fraction(17, 20) and q(2400.3) == Fraction(24003, 10) and q("0.03") == Fraction(3, 100)
    assert floor_step(Fraction(155200), 1000) == 155000 and floor_step(Fraction(999999, 1000), 1000) == 0
    assert exact_vnd(Fraction(121550)) == 121550
    with pytest.raises(NonIntegralAmount):
        exact_vnd(Fraction(1, 2))
    x = Fraction(1, 3) + 86666
    assert from_rational_text(to_rational_text(x)) == x and str(to_numeric_2(x)) == "86666.33"
    with pytest.raises(TypeError):
        q(True)


# ---- allocation (Section 15.3) --------------------------------------------------------------

def test_allocation_feasibility_conditions() -> None:
    P = {"a": Fraction(100), "b": Fraction(100)}
    w = {"a": Fraction(1), "b": Fraction(1)}
    lo = {"a": Fraction(40), "b": Fraction(40)}
    hi = {"a": Fraction(80), "b": Fraction(80)}
    assert pool.allocate_two_sided(Fraction(161), P, w, lo, hi).status == "INFEASIBLE_UPPER_BOUND"      # F3
    assert pool.allocate_two_sided(Fraction(79), P, w, lo, hi).status == "INFEASIBLE_LOWER_BOUND"       # F2
    assert pool.allocate_two_sided(Fraction(160), P, w, lo, hi).fares == hi                              # = sum Cap
    assert pool.allocate_two_sided(Fraction(80), P, w, lo, hi).fares == lo                               # = sum Floor
    assert pool.allocate_two_sided(Fraction(10), {}, {}, {}, {}).status == "EMPTY_SET"
    bad = dict(lo, a=Fraction(81))
    assert pool.allocate_two_sided(Fraction(120), P, w, bad, hi).status == "INFEASIBLE_INDIVIDUAL_BOUNDS"  # F1
    with pytest.raises(ValueError):
        pool.allocate_two_sided(Fraction(120), P, dict(w, a=Fraction(0)), lo, hi)


def test_one_rider_at_cap_and_one_at_floor_at_the_same_time() -> None:
    """The case the sequential "Fixed" loop can get wrong (Section 15.3.4): three riders, one capped,
    one floored, one in between, total exact."""
    P = {"cap": Fraction(100000), "mid": Fraction(100000), "floor": Fraction(100000)}
    w = {"cap": Fraction(10000), "mid": Fraction(100000), "floor": Fraction(1000000)}
    lo = {k: Fraction(40000) for k in P}
    hi = {k: Fraction(80000) for k in P}
    a = pool.allocate_two_sided(Fraction(190000), P, w, lo, hi)
    assert a.status == "OK" and sum(a.fares.values()) == 190000
    assert a.fares["cap"] == 80000 and a.fares["floor"] == 40000 and a.fares["mid"] == 70000


# ---- gates (Section 14) --------------------------------------------------------------------

def test_gate1_boundary_is_inclusive(car: CarUrbanParams) -> None:
    assert pool.gate1(car, Fraction(261600), [194000, 133000])          # = 0.8 x 327.000
    assert not pool.gate1(car, Fraction(261601), [194000, 133000])


def test_gate1_rejects_a_plan_that_saves_too_little(car: CarUrbanParams) -> None:
    res = pool.price_new_plan(car, [R("A", 194000, 40, "0.25"), R("B", 133000, 28)], 23000, 60 * 52, 4)
    assert not res.ok and res.reason == "GATE1_PASSENGER_SHAREABILITY" and res.event == "POOL_SHAREABILITY_REJECTED"


def test_gate2a_payout_and_2b_hourly_rate_boundaries(car: CarUrbanParams) -> None:
    riders = [R("A", 194000, 40), R("B", 133000, 28)]
    g = pool.gate2(car, 248000, Fraction(52 * 60), riders)
    assert g.passed_2a and g.passed_2b and g.payout == 210800
    # 2A around the bound max (0.80 x P_i) = 155.200: 0.85 x 182.588 = 155.199,8 fails, 0.85 x 182.589 passes
    assert not pool.gate2(car, 182588, Fraction(30 * 60), riders).passed_2a
    assert pool.gate2(car, 182589, Fraction(30 * 60), riders).passed_2a
    # 2B: the scenario of Section 14.2 (more stops, tiny distance gain) - rate below the single ride
    g = pool.gate2(car, 248000, Fraction(56 * 60) + 40, riders)   # 210.800 / (56,67 / 60) < 232.800
    assert g.passed_2a and not g.passed_2b
    exact_t = Fraction(210800 * 60, 232800) * 60                 # T_plan giving exactly 232.800 VND/h
    assert pool.gate2(car, 248000, exact_t, riders).passed_2b
    assert not pool.gate2(car, 248000, exact_t + Fraction(1, 1000), riders).passed_2b
    off = replace(car, enforce_hourly_gate=False)
    assert pool.gate2(off, 248000, Fraction(56 * 60) + 40, riders).passed_2b
    eps = replace(car, eps_hourly=Fraction(5, 100))                 # tolerance only when configured
    assert pool.gate2(eps, 248000, Fraction(56 * 60) + 40, riders).passed_2b


def test_hourly_gate_rejects_a_plan_in_price_new_plan(car: CarUrbanParams) -> None:
    res = pool.price_new_plan(car, [R("A", 194000, 40, "0.25"), R("B", 133000, 28)], 17500, 60 * 70, 4)
    assert not res.ok and res.reason in ("GATE2B_DRIVER_HOURLY_RATE", "GATE1_PASSENGER_SHAREABILITY")


# ---- bounds, seats, rounding -----------------------------------------------------------------

def test_floor_cap_and_seat_factor(car: CarUrbanParams) -> None:
    a1, a2 = R("A", 194000), R("A", 194000, seats=2)
    assert pool.cap(car, a1) == pool.cap(car, a2) == 155200            # P_i unchanged for 2 seats (12.2)
    assert pool.raw_floor(car, a1) == 77600 and pool.raw_floor(car, a2) == 104760
    assert pool.raw_floor(car, R("S", 30000)) == 20000                 # BASE
    assert pool.weight(car, a2) == pool.weight(car, a1) / Fraction(135, 100)
    tiny = R("T", 24000)                                               # Cap 19.200 < BASE: Floor = min(Cap, RawFloor)
    assert min(pool.cap(car, tiny), pool.raw_floor(car, tiny)) == 19200


def test_two_seat_quote_unmatched_below_private(car: CarUrbanParams) -> None:
    for P in (45000, 133000, 194000, 637000):
        pq = tariff.pool_quote_for(car, P)
        assert pq.quote <= P * Fraction(4, 5) < pq.unmatched < P


def test_rounding_never_rounds_up(car: CarUrbanParams) -> None:
    res = pool.price_new_plan(car, [R("A", 194000, 40, "0.25"), R("B", 133000, 28)], 17500, 52 * 60, 4)
    for x in res.prices.values():
        assert 0 <= x.rounding_absorbed < 1000 and x.fare_charged % 1000 == 0
        assert x.fare_charged <= x.quote <= x.quote_cap


# ---- dynamic insertion D1-D6 (Section 15.5) -----------------------------------------------

def first_plan(car: CarUrbanParams) -> pool.PoolPricing:
    return pool.price_new_plan(car, [R("A", 194000, 40, "0.25"), R("B", 133000, 28)], 17500, 52 * 60, 4)


def insertion(car: CarUrbanParams, *, lock_b: bool = True, open_: bool = True, overlap: bool = True,
              plan_fare: int = 288500, budget: int | None = None, new: pool.PoolRider | None = None,
              old_override: list | None = None) -> pool.InsertionInput:
    f = first_plan(car)
    A, B = f.prices["A"], f.prices["B"]
    old = old_override or [
        pool.PricedRider(R("A", 194000, 40, "0.28"), False, A.fare_exact, A.fare_charged, None),
        pool.PricedRider(R("B", 133000, 28), lock_b, B.fare_exact, B.fare_charged, B.fare_charged if lock_b else None)]
    t_s = Fraction(60 * 60)
    d_m = Fraction(plan_fare - 20000 - 30000 - 20000, 11000) * 1000
    return pool.InsertionInput(open_, f.plan_fare, old, new or R("C", 64000, 15, "0.05"), budget, overlap, d_m, t_s, 6)


def test_d1_each_condition(car: CarUrbanParams) -> None:
    assert pool.price_insertion(car, insertion(car, open_=False)).reason == "D1_PLAN_NOT_OPEN"
    assert pool.price_insertion(car, insertion(car, overlap=False)).reason == "D1_NO_CO_RIDING_OVERLAP"
    f = first_plan(car)
    all_locked = [pool.PricedRider(R("A", 194000, 40), True, f.prices["A"].fare_exact, 143000, 143000),
                  pool.PricedRider(R("B", 133000, 28), True, f.prices["B"].fare_exact, 105000, 105000)]
    assert pool.price_insertion(car, insertion(car, old_override=all_locked)).reason == "D1_NO_UNLOCKED_RIDER"
    off = replace(car, allow_dynamic_insertion_after_partial_lock=False)
    assert pool.price_insertion(off, insertion(off)).reason == "D1_PARTIAL_LOCK_INSERTION_DISABLED"


def test_d3_upper_bound(car: CarUrbanParams) -> None:
    """Delta PlanFare > Cap_C = 51.200 -> INFEASIBLE_UPPER_BOUND (D3)."""
    ok = pool.price_insertion(car, insertion(car, plan_fare=248500 + 51200))
    bad = pool.price_insertion(car, insertion(car, plan_fare=248500 + 51201))
    assert bad.reason == "INFEASIBLE_UPPER_BOUND" and bad.event == "POOL_ALLOCATION_INFEASIBLE_CAP"
    assert ok.reason != "INFEASIBLE_UPPER_BOUND"


def test_d4_lower_bound(car: CarUrbanParams) -> None:
    """A's fare already at its floor and a tiny Delta PlanFare -> sum Floor > TargetFare_U (D4)."""
    old = [pool.PricedRider(R("A", 194000, 40, "0.28"), False, Fraction(77600), 77000, None),
           pool.PricedRider(R("B", 133000, 28), True, Fraction(170900), 170000, 170000)]
    x = insertion(car, old_override=old, plan_fare=248500 + 10000)
    x = replace(x, plan_fare_old=Fraction(248500))
    res = pool.price_insertion(car, x)
    assert res.reason == "INFEASIBLE_LOWER_BOUND" and res.event == "POOL_ALLOCATION_INFEASIBLE_FLOOR"


def test_d5_frozen_group_and_no_increase(car: CarUrbanParams) -> None:
    res = pool.price_insertion(car, insertion(car))
    assert res.ok
    f = first_plan(car)
    assert res.prices["B"].group == "L" and res.prices["B"].fare_exact == f.prices["B"].fare_exact
    assert res.prices["B"].fare_charged == f.prices["B"].fare_charged
    assert res.prices["A"].fare_exact <= f.prices["A"].fare_exact
    assert res.prices["A"].fare_charged <= f.prices["A"].fare_charged
    assert sum(x.fare_exact for x in res.prices.values()) == res.plan_fare


def test_d5_gate2_after_rounding_on_the_whole_plan(car: CarUrbanParams) -> None:
    """Same Delta PlanFare but a much longer T_plan: gate 2B fails after the allocation."""
    x = replace(insertion(car), t_plan_s=Fraction(90 * 60),
                d_plan_m=Fraction(288500 - 20000 - 45000 - 20000, 11000) * 1000)
    res = pool.price_insertion(car, x)
    assert not res.ok and res.reason == "GATE2B_DRIVER_HOURLY_RATE" and res.prices


def test_d6_budget_of_the_new_rider(car: CarUrbanParams) -> None:
    unmatched_c = tariff.pool_quote_for(car, 64000).unmatched
    assert pool.price_insertion(car, insertion(car, budget=unmatched_c)).ok
    res = pool.price_insertion(car, insertion(car, budget=unmatched_c - 1))
    assert res.reason == "D6_BUDGET_EXCEEDED"


def test_inconsistent_stored_state_is_rejected(car: CarUrbanParams) -> None:
    x = insertion(car)
    assert pool.price_insertion(car, replace(x, plan_fare_old=x.plan_fare_old + 1)).reason == \
        "PLAN_PRICING_STATE_INCONSISTENT"
    half = [replace(x.old[0], fare_exact_old=None), x.old[1]]
    assert pool.price_insertion(car, replace(x, old=half)).reason == "PLAN_PRICING_STATE_INCONSISTENT"
    two_unpriced = [pool.PricedRider(R("A", 194000, 40), False, None, None, None),
                    pool.PricedRider(R("B", 133000, 28), False, None, None, None)]
    assert pool.price_insertion(car, replace(x, old=two_unpriced, plan_fare_old=None)).reason == \
        "PLAN_PRICING_STATE_INCONSISTENT"
    locked_without_price = [x.old[0], replace(x.old[1], final_price=None)]
    assert pool.price_insertion(car, replace(x, old=locked_without_price)).reason == "PLAN_PRICING_STATE_INCONSISTENT"


def test_first_match_uses_cap_and_no_previous_price(car: CarUrbanParams) -> None:
    """Plan with one booking (never allocated) + the new one: EffectiveCap = Cap for both (15.3.2)."""
    old = [pool.PricedRider(R("A", 194000, 40, "0.25"), False, None, None, None)]
    x = pool.InsertionInput(True, None, old, R("B", 133000, 28), None, True, Fraction(17500), Fraction(52 * 60), 4)
    res = pool.price_insertion(car, x)
    assert res.ok and res.prices["A"].effective_cap == 155200 and res.prices["B"].effective_cap == 106400
    assert res.prices["A"].fare_charged == 143000 and res.prices["B"].fare_charged == 105000
    assert res.prices["B"].group == "NEW"


def test_invalid_rider_input(car: CarUrbanParams) -> None:
    assert pool.price_new_plan(car, [R("A", 194000)], 1000, 600, 2).reason == "INVALID_INPUT"
    assert pool.price_new_plan(car, [R("A", 194000, seats=3), R("B", 133000)], 1000, 600, 4).reason == "INVALID_INPUT"
    assert pool.price_new_plan(car, [R("A", 194000, t_min=0), R("B", 133000)], 1000, 600, 4).reason == "INVALID_INPUT"
    assert pool.price_new_plan(car, [R("A", 194000), R("A", 133000)], 1000, 600, 4).reason == "INVALID_INPUT"


def test_final_price_at_lock(car: CarUrbanParams) -> None:
    with pytest.raises(ValueError):
        pool.final_price_at_lock(car, 194000, True, 156000, "NONE")      # above Quote_i: never
    assert pool.final_price_at_lock(car, 194000, False, None, "CORIDER_CANCELLED_EARLY") == 174000


# ---- parameters -------------------------------------------------------------------------------

def test_baseline_parameters_load_and_validate() -> None:
    p = PricingParams.from_sections(BASELINE["pricing_version"], BASELINE["pool_policy_version"], BASELINE)
    assert p.car.commission_pool == p.car.platform_net_pool + p.car.fund_rate == Fraction(15, 100)
    assert p.car.on_lower_bound_infeasible == "REJECT" and p.car.enforce_hourly_gate is True
    assert p.intercity_pool.commission_topup == p.intercity_private.commission


@pytest.mark.parametrize(("key", "value"), [
    ("d_min", 0.65), ("d_max", 0.2), ("commission_pool_total", 0.16), ("on_lower_bound_infeasible", "CLAMP"),
    ("rounding_step_vnd", 500), ("party_seat_surcharge_gamma", 0.6), ("base_vnd", 20500), ("d_matched_typical", 0.7),
    ("enforce_driver_hourly_rate_gate", "yes"), ("max_party_seats_pool", 3)])
def test_out_of_domain_parameters_are_refused(key: str, value: object) -> None:
    with pytest.raises(PricingConfigError):
        CarUrbanParams.from_section(dict(BASELINE["car_urban"], **{key: value}))
