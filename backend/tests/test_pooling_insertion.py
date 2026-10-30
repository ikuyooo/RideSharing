"""P2.3 - dynamic insertion aware of the running vehicle (Revision 9 Section 36) and
the 11 hard constraints (Section 7), checked against the independent reference in
tests/p2_reference.py on 10 000 seeded random scenarios."""

import math
import random
import uuid
from datetime import UTC, datetime, timedelta

import pytest

from app.modules.candidate.constraints import (
    EXISTING_POOL_PLAN,
    HARD_CONSTRAINTS,
    NEW_SINGLE_VEHICLE,
    DriverState,
)
from app.modules.pooling.insertion import DROPOFF, PICKUP, Params, PlanState, RiderSpec, Stop, insert
from tests import p2_reference as ref

NOW = datetime(2026, 10, 29, 8, 0, tzinfo=UTC)
PARAMS = Params(dwell_s=60, k_max_stops=8, location_stale_s=120, per_km_vnd=11000, per_min_vnd=500, stop_fee_vnd=5000)
POOL = "CAR_URBAN_POOL"


def driver(**kw: object) -> DriverState:
    base = dict(driver_id=uuid.uuid4(), availability="BUSY", location_age_s=5, kyc_status="VERIFIED",
                accepts_urban=True, pool_enabled=True, accepts_intercity=False, max_additional_pickups=3,
                max_driver_detour_km=None, max_driver_detour_min=None, vehicle_id=uuid.uuid4(),
                vehicle_type="CAR4", capacity=4, vehicle_active=True)
    return DriverState(**(base | kw))  # type: ignore[arg-type]


def rider(ref_: str, direct_m: float, direct_s: float, *, onboard: bool = False, seats: int = 1,
          window: tuple[float, float] = (0, 1200), **kw: object) -> RiderSpec:
    base = dict(ref=ref_, seats=seats, onboard=onboard,
                pickup_window=None if onboard else (NOW + timedelta(seconds=window[0]), NOW + timedelta(seconds=window[1])),
                actual_pickup=NOW - timedelta(seconds=300) if onboard else None, traveled_m=2000.0 if onboard else 0.0,
                direct_distance_m=direct_m, direct_duration_s=direct_s, max_detour_ratio=0.30,
                max_in_vehicle_s=direct_s * 1.5 + 600, latest_arrival=None, max_price_vnd=100000, budget_max_vnd=None)
    return RiderSpec(**(base | kw))  # type: ignore[arg-type]


def line_matrix(xs: list[float], speed: float = 10.0) -> tuple[list[list[float]], list[list[float]]]:
    """Points on a line (metres): D = |a - b|, T = D / speed."""
    D = [[abs(a - b) for b in xs] for a in xs]
    return D, [[d / speed for d in row] for row in D]


def test_exactly_eleven_hard_constraints() -> None:
    assert list(HARD_CONSTRAINTS) == [f"HC{i:02d}" for i in range(1, 12)]


def test_new_rider_goes_between_on_a_straight_line() -> None:
    # nodes: 0 vehicle at 0 m, 1 A-dropoff at 10 km, 2 new P at 2 km, 3 new Q at 6 km
    D, T = line_matrix([0, 10000, 2000, 6000])
    a = rider("A", 12000, 1200, onboard=True)  # 2000 m traveled + 10000 m ahead = direct
    state = PlanState(uuid.uuid4(), 3, driver(), 0, NOW, completed_stops=1,
                      remaining=(Stop(1, DROPOFF, "A"),), riders=(a,))
    new = rider("new", 4000, 400)
    rep = insert(state, new, 2, 3, D, T, POOL, EXISTING_POOL_PLAN, (True, ""), PARAMS)
    assert rep.best is not None and rep.options_tried == 3
    assert [s.ref + s.kind[0] for s in rep.best.chain] == ["newP", "newD", "AD"]
    assert rep.best.added_distance_m == 0 and rep.best.pricing_check == "PENDING_P3"
    # The onboard rider is part of the evaluation: traveled + remaining distance.
    rider_a = next(r for r in rep.best.evaluation.riders if r.ref == "A")
    assert rider_a.onboard and rider_a.ride_distance_m == 12000


def test_onboard_rider_constraints_block_an_insertion() -> None:
    """Section 7 global rule: one old rider violating any constraint rejects the option."""
    # vehicle 0 m, A dropoff 4 km; new P at 9 km behind -> going there first pushes A over its detour.
    D, T = line_matrix([0, 4000, 9000, 9500])
    a = rider("A", 6000, 600, onboard=True, traveled_m=2000)  # 2000 + 4000 = direct, detour 0
    state = PlanState(uuid.uuid4(), 1, driver(), 0, NOW, 1, (Stop(1, DROPOFF, "A"),), (a,))
    rep = insert(state, rider("new", 500, 50, window=(0, 3000)), 2, 3, D, T, POOL, EXISTING_POOL_PLAN, (True, ""), PARAMS)
    # P before A's dropoff makes A ride 2000 + 9000 + 5500 > 1.3 x 6000; P after A's dropoff is fine.
    assert rep.best is not None and [s.ref for s in rep.best.chain] == ["A", "new", "new"]
    assert rep.rejections["HC05"] >= 1


def test_running_vehicle_never_inserts_before_the_current_position() -> None:
    D, T = line_matrix([0, 3000, 6000, 1000, 7000])
    a, b = rider("A", 8000, 800, onboard=True), rider("B", 4000, 400, window=(0, 900))
    state = PlanState(uuid.uuid4(), 7, driver(), 0, NOW, completed_stops=2,   # S_0, S_1 done
                      remaining=(Stop(1, PICKUP, "B"), Stop(2, DROPOFF, "A"), Stop(4, DROPOFF, "B")), riders=(a, b))
    rep = insert(state, rider("new", 6000, 600), 3, 4, D, T, POOL, EXISTING_POOL_PLAN, (True, ""), PARAMS)
    assert rep.options_tried == 10  # m_f = 4 -> 4 x 5 / 2 position pairs, all AFTER S_curr
    assert rep.best is not None and rep.best.evaluation.total_stops == 2 + 5


def test_k_max_and_additional_pickups() -> None:
    D, T = line_matrix([0, 1000, 2000, 3000, 4000, 5000, 6000, 7000])
    riders = (rider("A", 3000, 300, window=(0, 3000)), rider("B", 3000, 300, window=(0, 3000)))
    rem = (Stop(1, PICKUP, "A"), Stop(2, PICKUP, "B"), Stop(4, DROPOFF, "A"), Stop(5, DROPOFF, "B"))
    full = PlanState(uuid.uuid4(), 1, driver(), 0, NOW, completed_stops=3, remaining=rem, riders=riders)
    rep = insert(full, rider("new", 2000, 200), 3, 6, D, T, POOL, EXISTING_POOL_PLAN, (True, ""), PARAMS)
    assert rep.best is None and rep.rejections["HC07"] == rep.options_tried  # 3 + 4 + 2 = 9 > 8
    limited = PlanState(uuid.uuid4(), 1, driver(max_additional_pickups=1), 0, NOW, 0, rem, riders)
    rep = insert(limited, rider("new", 2000, 200), 3, 6, D, T, POOL, EXISTING_POOL_PLAN, (True, ""), PARAMS)
    assert rep.best is None and set(rep.rejections) == {"HC07"}


def test_segment_capacity() -> None:
    D, T = line_matrix([0, 5000, 1000, 4000])
    a = rider("A", 7000, 700, onboard=True, seats=2)
    b = rider("B", 7000, 700, onboard=True, seats=1)
    state = PlanState(uuid.uuid4(), 1, driver(), 0, NOW, 2, (Stop(1, DROPOFF, "A"), Stop(1, DROPOFF, "B")), (a, b))
    rep = insert(state, rider("new", 3000, 300, seats=2, window=(0, 3000)), 2, 3, D, T, POOL,
                 EXISTING_POOL_PLAN, (True, ""), PARAMS)
    # 3 seats aboard until both drop at 5 km: the 2-seat booking only fits after them.
    assert rep.best is not None and [s.ref for s in rep.best.chain][:2] == ["A", "B"]
    assert rep.rejections["HC04"] >= 1


def test_same_gender_needs_verified_gender_on_overlap() -> None:
    D, T = line_matrix([0, 6000, 1000, 5000])
    a = rider("A", 6000, 600, onboard=True, traveled_m=0, same_gender=True, verified_gender="F")
    state = PlanState(uuid.uuid4(), 1, driver(), 0, NOW, 1, (Stop(1, DROPOFF, "A"),), (a,))
    male = rider("new", 4000, 400, verified_gender="M", window=(0, 9000))
    rep = insert(state, male, 2, 3, D, T, POOL, EXISTING_POOL_PLAN, (True, ""), PARAMS)
    # Every position where the two ride together is rejected; after A's dropoff there is no overlap.
    assert rep.rejections["HC11"] >= 1
    assert rep.best is None or [s.ref for s in rep.best.chain][0] == "A"
    unverified = rider("new", 4000, 400, verified_gender=None, window=(0, 9000))
    rep2 = insert(state, unverified, 2, 3, D, T, POOL, EXISTING_POOL_PLAN, (True, ""), PARAMS)
    assert rep2.best is None or [s.ref for s in rep2.best.chain][0] == "A"
    female = rider("new", 4000, 400, verified_gender="F", window=(0, 9000))
    rep3 = insert(state, female, 2, 3, D, T, POOL, EXISTING_POOL_PLAN, (True, ""), PARAMS)
    assert rep3.best is not None and [s.ref for s in rep3.best.chain][0] == "new"


def test_single_vehicle_is_insertion_into_an_empty_plan() -> None:
    D, T = line_matrix([0, 1500, 7500])
    idle = driver(availability="IDLE", vehicle_type="BIKE", capacity=1, pool_enabled=False, kyc_status="NONE")
    state = PlanState(None, None, idle, 0, NOW, 0, (), ())
    rep = insert(state, rider("new", 6000, 600, window=(180, 900)), 1, 2, D, T, "BIKE_URBAN",
                 NEW_SINGLE_VEHICLE, (True, ""), PARAMS)
    assert rep.best is not None and rep.options_tried == 1
    new = rep.best.evaluation.riders[0]
    assert new.planned_pickup == NOW + timedelta(seconds=180)  # 150 s away: waits for T_earliest
    busy = PlanState(None, None, driver(availability="BUSY", vehicle_type="BIKE", capacity=1), 0, NOW, 0, (), ())
    rep = insert(busy, rider("new", 6000, 600), 1, 2, D, T, "BIKE_URBAN", NEW_SINGLE_VEHICLE, (True, ""), PARAMS)
    assert rep.best is None and rep.rejections["HC01"] == 1


def test_booking_time_and_unroutable_leg_and_budget() -> None:
    D, T = line_matrix([0, 1000, 5000])
    D[1][2] = T[1][2] = None  # no road P -> Q in this profile
    idle = driver(availability="IDLE")
    state = PlanState(None, None, idle, 0, NOW, 0, (), ())
    rep = insert(state, rider("new", 4000, 400, budget_max_vnd=50000, max_price_vnd=60000), 1, 2, D, T,
                 "CAR_URBAN_PRIVATE", NEW_SINGLE_VEHICLE, (False, "lead time"), PARAMS)
    assert rep.best is None and {"HC02", "HC08", "HC09"} <= set(rep.rejections)


# ---------------------------------------------------------------------------
# 10 000 seeded random scenarios against the independent reference
# ---------------------------------------------------------------------------

def _scenario(rng: random.Random) -> tuple:
    n_old = rng.randint(0, 3)
    width = rng.choice([1500, 8000])  # a corridor (shared direction) or a square
    pts = [(rng.uniform(0, 8000), rng.uniform(0, width)) for _ in range(1 + 2 * n_old + 2)]

    def dist(a: tuple[float, float], b: tuple[float, float]) -> float:
        return math.dist(a, b) * rng.uniform(1.1, 1.4)

    D = [[0.0 if i == j else dist(a, b) for j, b in enumerate(pts)] for i, a in enumerate(pts)]
    T = [[d / rng.uniform(6, 12) for d in row] for row in D]
    if rng.random() < 0.05:
        i, j = rng.randrange(len(pts)), rng.randrange(len(pts))
        if i != j:
            D[i][j] = T[i][j] = None
    riders, order = [], []
    seats_aboard = 0
    waiting = []
    for k in range(n_old):
        p, q = 1 + 2 * k, 2 + 2 * k
        direct = D[p][q] or 1000.0
        onboard = rng.random() < 0.5
        seats = rng.choice([1, 1, 2]) if seats_aboard < 3 else 1
        seats_aboard += seats if onboard else 0
        r = RiderSpec(ref=f"r{k}", seats=seats, onboard=onboard,
                      pickup_window=None if onboard else (NOW + timedelta(seconds=rng.uniform(0, 600)),
                                                          NOW + timedelta(seconds=rng.uniform(900, 2400))),
                      actual_pickup=NOW - timedelta(seconds=rng.uniform(60, 900)) if onboard else None,
                      traveled_m=rng.uniform(0, 2000) if onboard else 0.0, direct_distance_m=direct,
                      direct_duration_s=direct / 9, max_detour_ratio=rng.choice([0.3, 0.5, 1.0, 2.0]),
                      max_in_vehicle_s=rng.uniform(1500, 6000),
                      latest_arrival=NOW + timedelta(seconds=rng.uniform(1800, 6000)) if rng.random() < 0.3 else None,
                      max_price_vnd=rng.randint(50, 200) * 1000,
                      budget_max_vnd=rng.randint(80, 250) * 1000 if rng.random() < 0.3 else None,
                      same_gender=rng.random() < 0.2, verified_gender=rng.choice(["F", "M", None]))
        riders.append(r)
        if onboard:
            order.append(Stop(q, DROPOFF, r.ref))
        else:
            waiting.append((Stop(p, PICKUP, r.ref), Stop(q, DROPOFF, r.ref)))
    rng.shuffle(order)
    for pick, drop in waiting:  # random positions, pickup always before its dropoff
        i = rng.randint(0, len(order))
        order.insert(i, pick)
        order.insert(rng.randint(i + 1, len(order)), drop)
    p_new, q_new = len(pts) - 2, len(pts) - 1
    new = RiderSpec(ref="new", seats=rng.choice([1, 2]), onboard=False,
                    pickup_window=(NOW + timedelta(seconds=rng.uniform(0, 600)), NOW + timedelta(seconds=rng.uniform(600, 2400))),
                    actual_pickup=None, traveled_m=0.0, direct_distance_m=D[p_new][q_new] or 1000.0,
                    direct_duration_s=(T[p_new][q_new] or 100.0), max_detour_ratio=rng.choice([0.3, 1.0]),
                    max_in_vehicle_s=(T[p_new][q_new] or 100.0) * 1.5 + 600,
                    latest_arrival=None, max_price_vnd=rng.randint(50, 200) * 1000,
                    budget_max_vnd=rng.randint(80, 250) * 1000 if rng.random() < 0.3 else None,
                    same_gender=rng.random() < 0.2, verified_gender=rng.choice(["F", "M", None]))
    drv = driver(max_additional_pickups=rng.choice([0, 2, 3, 3]), capacity=4,
                 max_driver_detour_km=rng.choice([None, None, 3.0, 8.0]), max_driver_detour_min=rng.choice([None, None, 15.0, 30.0]),
                 location_age_s=300 if rng.random() < 0.05 else 5)
    state = PlanState(uuid.uuid4(), 1, drv, 0, NOW, rng.choice([0, 0, 1, 2]), tuple(order), tuple(riders))
    return state, new, p_new, q_new, D, T


@pytest.mark.parametrize("chunk", range(10))
def test_random_insertions_have_zero_violations_and_are_optimal(chunk: int) -> None:
    feasible = 0
    for seed in range(chunk * 1000, (chunk + 1) * 1000):
        rng = random.Random(seed)
        state, new, p, q, D, T = _scenario(rng)
        rep = insert(state, new, p, q, D, T, POOL, EXISTING_POOL_PLAN, (True, ""), PARAMS)
        expected = ref.brute_force(state, new, p, q, D, T, POOL, EXISTING_POOL_PLAN, PARAMS.dwell_s,
                                   PARAMS.k_max_stops, PARAMS.location_stale_s, PARAMS.per_km_vnd, PARAMS.per_min_vnd)
        if rep.best is None:
            assert expected is None, f"seed {seed}: reference found a feasible insertion the algorithm missed"
            continue
        feasible += 1
        riders = {r.ref: r for r in state.riders} | {new.ref: new}
        bad = ref.violations(state, rep.best.chain, riders, D, T, POOL, EXISTING_POOL_PLAN, PARAMS.dwell_s,
                             PARAMS.k_max_stops, PARAMS.location_stale_s)
        assert not bad, f"seed {seed}: reference finds {bad}"
        assert expected is not None
        got = PARAMS.per_km_vnd * rep.best.added_distance_m / 1000 + PARAMS.per_min_vnd * rep.best.added_duration_s / 60
        assert got == pytest.approx(expected, abs=1e-6), f"seed {seed}: not the cheapest feasible insertion"
        # completed stops are never touched and S_curr stays first
        assert rep.best.evaluation.total_stops == state.completed_stops + len(rep.best.chain)
    assert feasible > 150  # the generator produces a meaningful share of feasible cases


class _OnlyTo(list):
    """A matrix row that refuses a destination outside the requested set."""

    def __init__(self, row: list, allowed: set[int]) -> None:
        super().__init__(row)
        self.allowed = allowed

    def __getitem__(self, j):  # type: ignore[no-untyped-def]
        assert j in self.allowed, f"insertion read a cell towards node {j}, which is not a requested destination"
        return super().__getitem__(j)


@pytest.mark.parametrize("chunk", range(3))
def test_insertion_reads_only_stop_destinations(chunk: int) -> None:
    """Proof obligation of the rectangular car table (OSRM optimisation): for every option the
    Section 36 insertion only reads D[u][v] / T[u][v] with v a stop ahead, P or Q - never the
    vehicle position S_curr. So a table whose destinations are exactly those nodes gives the
    same results as the full square table."""
    for seed in range(chunk * 1000, (chunk + 1) * 1000):
        rng = random.Random(seed)
        state, new, p, q, D, T = _scenario(rng)
        allowed = {s.node for s in state.remaining} | {p, q}
        guard_d = [_OnlyTo(row, allowed) for row in D]
        guard_t = [_OnlyTo(row, allowed) for row in T]
        rep = insert(state, new, p, q, guard_d, guard_t, POOL, EXISTING_POOL_PLAN, (True, ""), PARAMS)
        full = insert(state, new, p, q, D, T, POOL, EXISTING_POOL_PLAN, (True, ""), PARAMS)
        assert (rep.best is None) == (full.best is None)
        if rep.best is not None:
            assert rep.best.chain == full.best.chain and rep.best.delta_cost_vnd == full.best.delta_cost_vnd
