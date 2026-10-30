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
