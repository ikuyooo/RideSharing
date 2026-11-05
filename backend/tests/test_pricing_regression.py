"""P3 - fixed regression vectors of Revision 9 Sections 71.1 and 72.1, plus the worked numbers
of Sections 10.4, 16.1-16.3, 17, 18.4-18.5, 19.2, 25.2, 28.2 and 29, compared value by value
(not "it runs"). Parameters come from the locked baseline YAML, never from the test."""

from fractions import Fraction

import pytest
import yaml

from app.modules.pricing import pool, settlement, tariff
from app.modules.pricing.money import q
from app.modules.pricing.params import PricingParams
from tests.conftest import CONFIG_BASELINE


@pytest.fixture(scope="module")
def p() -> PricingParams:
    b = yaml.safe_load(CONFIG_BASELINE.read_text(encoding="utf-8"))
    return PricingParams.from_sections(b["pricing_version"], b["pool_policy_version"], b)


def km(x: float) -> Fraction:
    return q(x) * 1000


def minutes(x: float) -> Fraction:
    return q(x) * 60


def cents(x: Fraction) -> Fraction:
    """Round half-up to 0.01 VND - how Revision 9 prints Fare_exact."""
    return Fraction(int(x * 100 + Fraction(1, 2)), 100)


def rider(ref: str, P: int, t_min: float, detour: str = "0", seats: int = 1, walk: str = "0") -> pool.PoolRider:
    return pool.PoolRider(ref, P, seats, minutes(t_min), q(detour), q(walk))


# ---- Section 71.1 vector 1 / Section 16.1 / Section 17 ----------------------------------

def test_71_1_vector_1_two_riders_matched(p: PricingParams) -> None:
    P_A = tariff.private_fare(p.car, km(14.0), minutes(40))
    P_B = tariff.private_fare(p.car, km(9.0), minutes(28))
    assert (P_A, P_B) == (194000, 133000)
    res = pool.price_new_plan(p.car, [rider("A", P_A, 40, "0.25"), rider("B", P_B, 28)], km(17.5), minutes(52), 4)
    assert res.ok, res
    assert res.plan_fare == 248500
    assert pool.gate1(p.car, res.plan_fare, [P_A, P_B])
    A, B = res.prices["A"], res.prices["B"]
    assert (A.floor, A.effective_cap, B.floor, B.effective_cap) == (77600, 155200, 53200, 106400)
    assert (A.weight, B.weight) == (242500, 133000)
    assert cents(A.fare_exact) == q("143304.26") and cents(B.fare_exact) == q("105195.74")
    assert A.fare_exact + B.fare_exact == 248500                       # N1, exactly
    assert (A.fare_charged, B.fare_charged) == (143000, 105000)
    assert cents(A.rounding_absorbed) == q("304.26") and cents(B.rounding_absorbed) == q("195.74")
    assert A.fare_charged + B.fare_charged == 248000
    assert A.rounding_absorbed + B.rounding_absorbed == 500
    g = res.gate
    assert g.payout == 210800 and int(g.hourly) == 243230 and round(g.hourly) == 243231
    assert g.max_private_payout == 155200 and g.max_private_hourly == 232800
    sa, sb = settlement.settle_pool_matched(p, 143000), settlement.settle_pool_matched(p, 105000)
    assert (sa.driver_base, sa.platform_net, sa.fund_contribution) == (121550, 17160, 4290)
    assert (sb.driver_base, sb.platform_net, sb.fund_contribution) == (89250, 12600, 3150)
    assert sa.driver_base + sb.driver_base == 210800
    assert sa.platform_net + sb.platform_net == 29760
    assert sa.fund_contribution + sb.fund_contribution == 7440
    # Section 17.3 table: income per hour of the single rides
    assert settlement.settle_fixed(p, "CAR_URBAN_PRIVATE", 194000).driver_base == 155200
    assert settlement.settle_fixed(p, "CAR_URBAN_PRIVATE", 133000).driver_base == 106400


def test_16_1_reference_allocations(p: PricingParams) -> None:
    """Section 16.1 table of the two benchmark methods (proportional, Shapley = equal split of S)."""
    S = 327000 - 248500
    assert round(194000 - Fraction(S * 194000, 327000)) == 147428      # printed to the dong
    assert round(133000 - Fraction(S * 133000, 327000)) == 101072
    assert 194000 - Fraction(S, 2) == 154750 and 133000 - Fraction(S, 2) == 93750


# ---- Section 71.1 vector 2 / Sections 18.4, 18.5 -------------------------------------------

def test_71_1_vector_2_unmatched_and_anti_sabotage(p: PricingParams) -> None:
    pq = tariff.pool_quote_for(p.car, 194000)
    assert (pq.quote, pq.gap, pq.unmatched) == (155000, 39000, 174000)
    s = settlement.settle_pool_unmatched(p, 194000, 174000, "NO_COMPATIBLE")
    assert (s.driver_base, s.guarantee, s.total_driver, s.platform_net, s.fund_contribution) == \
        (147900, 7300, 155200, 26100, 0)
    d = settlement.settle_pool_unmatched(p, 194000, 155000, "DRIVER_DECLINED")
    assert (d.gross_charged, d.guarantee, d.total_driver, d.platform_net) == (155000, 0, 131750, 23250)
    assert 155200 - d.total_driver == 23450
    r = settlement.settle_pool_unmatched(p, 194000, 174000, "PASSENGER_REJECTED_POOL")   # row 5
    assert (r.total_driver, r.guarantee) == (155200, 7300)
    with pytest.raises(ValueError):                    # the cause decides the locked price
        settlement.settle_pool_unmatched(p, 194000, 174000, "DRIVER_DECLINED")
    assert pool.final_price_at_lock(p.car, 194000, False, None, "NO_COMPATIBLE") == 174000
    assert pool.final_price_at_lock(p.car, 194000, False, None, "DRIVER_DECLINED") == 155000
    assert pool.final_price_at_lock(p.car, 194000, True, 143000, "NONE") == 143000


def test_18_5_row_4_corider_cancelled_late(p: PricingParams) -> None:
    """A keeps its locked 143.000; the fund tops the driver up to 155.200 after counting the driver's
    share of B's cancellation fee (interpretation SF-P3-04)."""
    s = settlement.settle_pool_matched(p, 143000, "CORIDER_CANCELLED_LATE", private=194000,
                                       corider_cancel_to_driver=15500)
    assert s.driver_base == 121550 and s.fund_contribution == 4290
    assert s.guarantee == 155200 - 121550 - 15500 and s.total_driver + 15500 == 155200


# ---- Section 71.1 vector 3 / Section 16.2 --------------------------------------------------

FOUR = [("1", 45000, "0.30", "0.20"), ("2", 205000, "0", "0"), ("3", 205000, "0", "0"), ("4", 205000, "0", "0")]


def four(p: PricingParams, target: int, mode: str = "REJECT") -> pool.Allocation:
    car = p.car if mode == "REJECT" else type(p.car)(**{**p.car.__dict__, "on_lower_bound_infeasible": mode})
    riders = [pool.PoolRider(r, P, 1, Fraction(1800), q(d), q(w)) for r, P, d, w in FOUR]
    caps = {r.ref: pool.cap(car, r) for r in riders}
    P, w, floor, caps = pool._bounds(car, riders, caps)
    assert floor == {"1": 20000, "2": 82000, "3": 82000, "4": 82000}
    assert caps == {"1": 36000, "2": 164000, "3": 164000, "4": 164000}
    assert w == {"1": 76500, "2": 205000, "3": 205000, "4": 205000}
    assert sum(floor.values()) == 266000 and sum(caps.values()) == 528000
    return pool._allocate(car, Fraction(target), P, w, floor, caps)


def test_71_1_vector_3a_floor_binds(p: PricingParams) -> None:
    a = four(p, 280000)
    assert a.status == "OK"
    assert a.fares["1"] == 20000
    assert all(cents(a.fares[k]) == q("86666.67") for k in "234")
    assert sum(a.fares.values()) == 280000
    assert [tariff.floor_step(a.fares[k], 1000) for k in "1234"] == [20000, 86000, 86000, 86000]
    # without the floor the unbounded share of rider 1 would be 2.960,95
    assert cents(45000 - Fraction(380000 * 76500, 691500)) == q("2960.95")


def test_71_1_vector_3b_lower_bound_infeasible(p: PricingParams) -> None:
    assert p.car.on_lower_bound_infeasible == "REJECT"          # baseline: never CLAMP_TO_BASE silently
    a = four(p, 220000)
    assert a.status == "INFEASIBLE_LOWER_BOUND" and a.fares is None
    c = four(p, 220000, mode="CLAMP_TO_BASE")                   # the optional mode, only when configured
    assert c.status == "OK" and c.clamped_to_base
    assert c.fares["1"] == 20000 and all(cents(c.fares[k]) == q("66666.67") for k in "234")
    assert [tariff.floor_step(c.fares[k], 1000) for k in "234"] == [66000] * 3


def test_71_1_vector_3c_two_seat_booking(p: PricingParams) -> None:
    res = pool.price_new_plan(p.car, [rider("A", 194000, 40, "0.25", seats=2), rider("B", 133000, 28)],
                              km(17.5), minutes(52), 4)
    assert res.ok
    A, B = res.prices["A"], res.prices["B"]
    assert (A.quote, A.unmatched) == (155000, 174000) and A.unmatched < 194000
    assert cents(A.fare_exact) == q("148895.75") and A.fare_charged == 148000
    assert cents(B.fare_exact) == q("99604.25") and B.fare_charged == 99000
    assert 143000 < A.fare_charged <= A.quote
    assert A.floor == q("104760")                               # 0.40 x 194.000 x 1.35 (0.54 P_A)


# ---- Section 71.1 vector 4 / Section 16.3 --------------------------------------------------

def test_71_1_vector_4_insert_c_while_b_is_locked(p: PricingParams) -> None:
    first = pool.price_new_plan(p.car, [rider("A", 194000, 40, "0.25"), rider("B", 133000, 28)],
                                km(17.5), minutes(52), 4)
    A0, B0 = first.prices["A"], first.prices["B"]
    old = [pool.PricedRider(rider("A", 194000, 40, "0.28"), False, A0.fare_exact, A0.fare_charged, None),
           pool.PricedRider(rider("B", 133000, 28), True, B0.fare_exact, B0.fare_charged, B0.fare_charged)]
    # Section 16.3 states PlanFare_new = 288.500 and T_plan' = 60 min; D_plan follows from Section 13
    t_s = minutes(60)
    d_m = Fraction(288500 - 20000 - 500 * 60 - 5000 * 4, 11000) * 1000
    assert pool.plan_fare(p.car, d_m, t_s, 6) == 288500
    x = pool.InsertionInput(plan_open=True, plan_fare_old=first.plan_fare, old=old,
                            new=rider("C", 64000, 15, "0.05"), new_budget_max=None, co_riding_overlap=True,
                            d_plan_m=d_m, t_plan_s=t_s, total_stops=6)
    res = pool.price_insertion(p.car, x)
    assert res.ok, res
    A, B, C = res.prices["A"], res.prices["B"], res.prices["C"]
    assert cents(res.target_fare_u) == q("183304.26")
    assert B.group == "L" and B.fare_exact == B0.fare_exact and B.fare_charged == 105000    # frozen
    assert A.effective_cap == A0.fare_exact and C.effective_cap == 51200
    assert (A.floor, C.floor) == (77600, 25600)
    assert (A.weight, C.weight) == (248320, 67200)
    assert A.fare_charged == 135000 and A.fare_charged <= 143000
    assert C.fare_charged == 48000 and C.fare_exact <= 51200
    assert A.fare_exact + B.fare_exact + C.fare_exact == 288500
    assert A.fare_charged + B.fare_charged + C.fare_charged == 288000
    assert res.gate.payout == 244800 and res.gate.hourly == 244800 and res.gate.max_private_hourly == 232800
    # SF-P3-01: Revision 9 prints 135.228,10 / 48.076,16; the exact solution of the same equations
    # (and the unbounded formula of 15.2, since no bound binds) is 135.213,09 / 48.091,17.
    assert cents(A.fare_exact) == q("135213.09") and cents(C.fare_exact) == q("48091.17")
    S_U = 258000 - res.target_fare_u
    assert A.fare_exact == 194000 - S_U * Fraction(248320, 248320 + 67200)


# ---- Section 72.1 and the other worked numbers --------------------------------------------

def test_72_1_fixed_fares(p: PricingParams) -> None:
    bike = tariff.bike_fare(p.bike, km(14.0), minutes(35))
    assert bike == 81000
    s = settlement.settle_fixed(p, "BIKE_URBAN", bike)
    assert (s.driver_base, s.platform_net) == (64800, 16200)
    ip = tariff.intercity_private_fare(p.intercity_private, km(65.0))
    assert ip == 637000
    s = settlement.settle_fixed(p, "CAR_INTERCITY_PRIVATE", ip)
    assert (s.driver_base, s.platform_net) == (541450, 95550)
    ref = tariff.seat_reference(p.intercity_pool, p.intercity_private, ip)
    assert ref == 200000 and tariff.seat_price_band(p.intercity_pool, ref) == (180000, 220000)
    seat = lambda n: settlement.settle_intercity_pool(p, 200000 * n, "CONFIRMED")  # noqa: E731
    assert [seat(n).driver_base for n in (1, 2, 3, 4)] == [180000, 360000, 540000, 720000]
    assert [seat(n).platform_net for n in (1, 2, 3, 4)] == [20000, 40000, 60000, 80000]
    assert round(Fraction(540000, 541450) * 100, 2) == q("99.73") and round(Fraction(720000, 541450) * 100, 2) == q("132.98")
    t2 = tariff.topup_seat_price(p.intercity_pool, ip, 2)
    assert t2 == 318000 and tariff.topup_amount(t2, 200000, 1) == 118000
    s2 = settlement.settle_intercity_pool(p, 2 * t2, "CONFIRMED_TOPUP")
    assert (s2.gross_charged, s2.platform_net, s2.driver_base) == (636000, 95400, 540600)
    t1 = tariff.topup_seat_price(p.intercity_pool, ip, 1)
    assert t1 == 637000 and tariff.topup_amount(t1, 200000, 1) == 437000
    s1 = settlement.settle_intercity_pool(p, t1, "CONFIRMED_TOPUP")
    assert (s1.platform_net, s1.driver_base) == (95550, 541450)
    under = settlement.settle_intercity_pool(p, 2 * 200000, "CONFIRMED_UNDER_MIN")       # Section 29 step 2.3
    assert under.driver_base == 360000


def test_10_4_three_urban_services_side_by_side(p: PricingParams) -> None:
    assert tariff.bike_fare(p.bike, km(14.0), minutes(35)) == 81000
    assert tariff.private_fare(p.car, km(14.0), minutes(40)) == 194000
    assert tariff.fare_matched_estimate(p.car, 194000) == 145000        # Section 20.2 case 2


def test_19_2_fund_break_even_inputs(p: PricingParams) -> None:
    chi_a = settlement.settle_pool_unmatched(p, 194000, 174000, "NO_COMPATIBLE").guarantee
    qb = tariff.pool_quote_for(p.car, 133000)
    assert (qb.quote, qb.gap, qb.unmatched) == (106000, 27000, 119000)
    chi_b = settlement.settle_pool_unmatched(p, 133000, 119000, "NO_COMPATIBLE").guarantee
    assert (chi_a, chi_b) == (7300, 5250)
    thu = p.car.fund_rate * Fraction(143000 + 105000, 2)
    assert thu == 3720
    assert round(Fraction(chi_a) / (chi_a + thu) * 100, 2) == q("66.24")
    e_chi = Fraction(chi_a + chi_b, 2)
    assert round(e_chi / (e_chi + thu) * 100, 2) == q("62.78")
    assert round(e_chi / (e_chi + 2 * thu) * 100, 2) == q("45.75")


def test_28_3_door_surcharge_and_28_4_booking_price(p: PricingParams) -> None:
    ds = tariff.door_surcharge(p.intercity_pool, pickup_in_zone=False, pickup_boundary_direct_km=2.0,
                               pickup_road_km=2.6, dropoff_in_zone=True, dropoff_boundary_direct_km=0,
                               dropoff_road_km=0)
    assert ds == tariff.DoorSurcharge(False, 10000)                      # floor(4.000 x 2,6 / 1.000) x 1.000
    assert tariff.booking_price(200000, 2, ds.amount) == 410000
    far = tariff.door_surcharge(p.intercity_pool, pickup_in_zone=False, pickup_boundary_direct_km=10.01,
                                pickup_road_km=12, dropoff_in_zone=True, dropoff_boundary_direct_km=0, dropoff_road_km=0)
    assert far.rejected
    edge = tariff.door_surcharge(p.intercity_pool, pickup_in_zone=False, pickup_boundary_direct_km=10.0,
                                 pickup_road_km=12, dropoff_in_zone=True, dropoff_boundary_direct_km=0, dropoff_road_km=0)
    assert not edge.rejected and edge.amount == 48000
    assert tariff.merged_seat_price(220000, 200000) == 200000 and tariff.merged_seat_price(190000, 200000) == 190000


def test_seat_price_band_validation(p: PricingParams) -> None:
    tariff.validate_seat_price(p.intercity_pool, 200000, 180000)
    tariff.validate_seat_price(p.intercity_pool, 200000, 220000)
    for bad in (179000, 221000, 200500):
        with pytest.raises(ValueError):
            tariff.validate_seat_price(p.intercity_pool, 200000, bad)
