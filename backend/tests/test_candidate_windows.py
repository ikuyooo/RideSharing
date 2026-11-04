"""OD-P2-03 (LOCAL_PROVISIONAL): default pickup window [T_earliest, T_latest] used by hard
constraint 3, for NOW and SCHEDULED requests, with and without a window given by the rider."""

import uuid
from datetime import UTC, datetime, timedelta

import pytest
import yaml

from app.modules.candidate.generator import booking_time_ok, pickup_window
from app.modules.trip.service import TripSnapshot
from tests.conftest import CONFIG_BASELINE

T0 = datetime(2026, 10, 30, 8, 0, tzinfo=UTC)


@pytest.fixture(scope="module")
def baseline() -> dict:
    return yaml.safe_load(CONFIG_BASELINE.read_text(encoding="utf-8"))


def trip(booking_type: str, preferred: datetime, earliest: datetime | None = None, latest: datetime | None = None,
         created: datetime = T0) -> TripSnapshot:
    return TripSnapshot(request_id=uuid.uuid4(), user_id=uuid.uuid4(), mode="URBAN", booking_type=booking_type,
                        allowed_service_codes=("BIKE_URBAN", "CAR_URBAN_PRIVATE", "CAR_URBAN_POOL"), passenger_count=1,
                        has_luggage=False, pickup=(105.8, 21.0), dropoff=(105.85, 21.03), preferred_departure=preferred,
                        earliest_departure=earliest, latest_departure=latest, latest_arrival=None, budget_max=None,
                        max_passenger_detour_ratio=None, max_in_vehicle_time_s=None, max_walk_m=None,
                        same_gender_coride=False, created_at=created, service_area_version="v")


def m(minutes: float) -> datetime:
    return T0 + timedelta(minutes=minutes)


def test_now_uses_the_section_2_2_window(baseline: dict) -> None:
    assert pickup_window(trip("NOW", T0), "BIKE_URBAN", baseline) == (m(3), m(15))
    assert pickup_window(trip("NOW", T0), "CAR_URBAN_PRIVATE", baseline) == (m(5), m(20))
    assert pickup_window(trip("NOW", T0), "CAR_URBAN_POOL", baseline) == (m(5), m(20))


def test_now_intersects_the_riders_own_window(baseline: dict) -> None:
    assert pickup_window(trip("NOW", T0, earliest=m(8), latest=m(12)), "CAR_URBAN_PRIVATE", baseline) == (m(8), m(12))
    assert pickup_window(trip("NOW", T0, earliest=m(1), latest=m(30)), "BIKE_URBAN", baseline) == (m(3), m(15))


def test_scheduled_without_window_gets_the_width_of_the_now_window(baseline: dict) -> None:
    pref = m(120)
    assert pickup_window(trip("SCHEDULED", pref), "BIKE_URBAN", baseline) == (pref, pref + timedelta(minutes=12))
    assert pickup_window(trip("SCHEDULED", pref), "CAR_URBAN_POOL", baseline) == (pref, pref + timedelta(minutes=15))


def test_scheduled_with_window_keeps_it(baseline: dict) -> None:
    pref = m(120)
    w = pickup_window(trip("SCHEDULED", pref, earliest=m(110), latest=m(140)), "CAR_URBAN_PRIVATE", baseline)
    assert w == (m(110), m(140))
    # only an earliest bound: the default width starts there
    w = pickup_window(trip("SCHEDULED", pref, earliest=m(110)), "CAR_URBAN_PRIVATE", baseline)
    assert w == (m(110), m(125))


def test_booking_time_rule_hc09(baseline: dict) -> None:
    assert booking_time_ok(trip("SCHEDULED", m(12 * 60)), "CAR_URBAN_PRIVATE", baseline)[0]
    assert not booking_time_ok(trip("SCHEDULED", m(12 * 60 + 1)), "CAR_URBAN_PRIVATE", baseline)[0]
    assert not booking_time_ok(trip("NOW", m(-1)), "BIKE_URBAN", baseline)[0]


@pytest.mark.parametrize("service", ["BIKE_URBAN", "CAR_URBAN_PRIVATE", "CAR_URBAN_POOL"])
def test_scheduled_pickup_never_before_the_chosen_time(baseline: dict, service: str) -> None:
    """OD-P2-03 (APPROVED_FOR_MVP): per service; a vehicle that can arrive early waits for the
    start of the window, which is never before the time the rider chose."""
    from app.modules.candidate.constraints import NEW_SINGLE_VEHICLE, DriverState
    from app.modules.pooling.insertion import Params, PlanState, RiderSpec, insert

    pref = m(180)
    for t in (trip("SCHEDULED", pref), trip("SCHEDULED", pref, earliest=m(170), latest=m(200))):
        lo, hi = pickup_window(t, service, baseline)
        assert lo == (t.earliest_departure or t.preferred_departure)
        bike = service == "BIKE_URBAN"
        drv = DriverState(driver_id=uuid.uuid4(), availability="IDLE", location_age_s=5, kyc_status="VERIFIED",
                          accepts_urban=True, pool_enabled=True, accepts_intercity=False, max_additional_pickups=2,
                          max_driver_detour_km=None, max_driver_detour_min=None, vehicle_id=uuid.uuid4(),
                          vehicle_type="BIKE" if bike else "CAR4", capacity=1 if bike else 4, vehicle_active=True)
        D = [[0, 500, 6500], [500, 0, 6000], [6500, 6000, 0]]
        T = [[d / 10 for d in row] for row in D]  # the driver is 50 s from P
        rider = RiderSpec(ref="new", seats=1, onboard=False, pickup_window=(lo, hi), actual_pickup=None,
                          traveled_m=0.0, direct_distance_m=6000, direct_duration_s=600, max_detour_ratio=0.3,
                          max_in_vehicle_s=1500, latest_arrival=None, max_price_vnd=None, budget_max_vnd=None)
        params = Params(dwell_s=60, k_max_stops=8, location_stale_s=120, per_km_vnd=11000, per_min_vnd=500,
                        stop_fee_vnd=5000)
        rep = insert(PlanState(None, None, drv, 0, T0, 0, (), ()), rider, 1, 2, D, T, service, NEW_SINGLE_VEHICLE,
                     booking_time_ok(t, service, baseline), params)
        assert rep.best is not None
        assert rep.best.evaluation.riders[0].planned_pickup == lo
