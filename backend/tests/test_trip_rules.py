"""P1.5 - pure Trip Intent rules: Section 2.3 classification and Section 6
allowed services / Section 2.2 & 72.2 booking-time rules. Inputs are explicit
values (no geometry, no OSRM); the baseline YAML supplies every threshold."""

from datetime import timedelta

import pytest
import yaml

from app.modules.trip import rules
from tests.conftest import CONFIG_BASELINE

BASELINE = yaml.safe_load(CONFIG_BASELINE.read_text(encoding="utf-8"))
BUFFER = float(BASELINE["spatial_and_service_areas"]["urban_boundary_buffer_km"])


class DistanceProbe:
    def __init__(self, km: float) -> None:
        self.km = km
        self.calls = 0

    def __call__(self) -> float:
        self.calls += 1
        return self.km


def classify(p_total: bool, d_total: bool, p_urban: bool, d_urban: bool, km: float = 1.0) -> tuple[rules.Classification, int]:
    probe = DistanceProbe(km)
    return rules.classify(p_total, d_total, p_urban, d_urban, probe, BUFFER), probe.calls


# --- Section 2.3 ---------------------------------------------------------------------


def test_buffer_comes_from_baseline() -> None:
    assert BUFFER == 15.0


@pytest.mark.parametrize("p_total,d_total", [(False, True), (True, False), (False, False)])
def test_step1_outside_total_area(p_total: bool, d_total: bool) -> None:
    result, calls = classify(p_total, d_total, False, False)
    assert result.error_code == "OUT_OF_SERVICE_AREA" and result.mode is None and calls == 0


def test_step2_both_urban_needs_no_distance() -> None:
    result, calls = classify(True, True, True, True, km=999)
    assert result.mode == "URBAN" and calls == 0 and result.direct_distance_km is None


@pytest.mark.parametrize("p_urban,d_urban", [(True, False), (False, True)])
def test_buffer_boundary_is_inclusive_at_15_km(p_urban: bool, d_urban: bool) -> None:
    at, _ = classify(True, True, p_urban, d_urban, km=15.0)
    above, _ = classify(True, True, p_urban, d_urban, km=15.000001)
    below, _ = classify(True, True, p_urban, d_urban, km=14.999999)
    assert (at.mode, at.step, at.direct_distance_km) == ("URBAN", "2b", 15.0)
    assert below.mode == "URBAN"
    assert (above.mode, above.step) == ("INTERCITY", "3a")


def test_step3_both_ends_outside_urban_rejected() -> None:
    result, calls = classify(True, True, False, False, km=3.0)
    assert result.error_code == "UNSUPPORTED_INTER_PROVINCE_ROUTE" and calls == 0


def test_routing_errors_propagate() -> None:
    from app.modules.routing.service import RouteNotFound

    def fail() -> float:
        raise RouteNotFound("NoRoute")

    with pytest.raises(RouteNotFound):
        rules.classify(True, True, True, False, fail, BUFFER)


# --- Section 6 / 2.2 / 72.2 -------------------------------------------------------------


def allowed(mode: str, lead: timedelta, vehicle: str = "ANY", ride: str = "ANY", pax: int = 1,
            luggage: bool = False) -> tuple[list[str], dict[str, rules.Rejection]]:
    ok, rejected = rules.allowed_services(mode, vehicle, ride, pax, luggage, lead, BASELINE)
    return ok, {r.service_code: r for r in rejected}


def test_urban_now_any_any_single_passenger() -> None:
    ok, _ = allowed("URBAN", timedelta(0))
    assert ok == ["BIKE_URBAN", "CAR_URBAN_PRIVATE", "CAR_URBAN_POOL"]


def test_intercity_never_offers_urban_services_g13() -> None:
    ok, rejected = allowed("INTERCITY", timedelta(days=4))
    assert ok == ["CAR_INTERCITY_PRIVATE", "CAR_INTERCITY_POOL"]
    assert rejected["BIKE_URBAN"].code == "MODE_MISMATCH"


def test_bike_excluded_for_groups_and_luggage_g13() -> None:
    _, two = allowed("URBAN", timedelta(0), pax=2)
    _, bags = allowed("URBAN", timedelta(0), luggage=True)
    assert two["BIKE_URBAN"].code == "PASSENGER_COUNT_EXCEEDED"
    assert bags["BIKE_URBAN"].code == "LUGGAGE_NOT_ALLOWED"


def test_urban_pool_party_limit_from_baseline() -> None:
    assert BASELINE["car_urban"]["max_party_seats_pool"] == 2
    ok2, _ = allowed("URBAN", timedelta(0), pax=2)
    ok3, rejected3 = allowed("URBAN", timedelta(0), pax=3)
    assert "CAR_URBAN_POOL" in ok2
    assert "CAR_URBAN_POOL" not in ok3 and rejected3["CAR_URBAN_POOL"].details["max_passengers"] == 2
    assert "CAR_URBAN_PRIVATE" in ok3


def test_urban_lead_time_12_hours_inclusive() -> None:
    ok_at, _ = allowed("URBAN", timedelta(hours=12))
    ok_after, rejected = allowed("URBAN", timedelta(hours=12, seconds=1))
    assert ok_at == ["BIKE_URBAN", "CAR_URBAN_PRIVATE", "CAR_URBAN_POOL"]
    assert ok_after == [] and rejected["CAR_URBAN_PRIVATE"].code == "LEAD_TIME_OUT_OF_WINDOW"


def test_intercity_pool_71h59m_rejected_with_private_suggestion() -> None:
    """Section 72.2: 71 h 59 min -> pool refused, CAR_INTERCITY_PRIVATE suggested."""
    ok, rejected = allowed("INTERCITY", timedelta(hours=71, minutes=59))
    assert ok == ["CAR_INTERCITY_PRIVATE"]
    pool = rejected["CAR_INTERCITY_POOL"]
    assert pool.code == "LEAD_TIME_OUT_OF_WINDOW"
    assert pool.details["suggested_service_code"] == "CAR_INTERCITY_PRIVATE"
    assert pool.details["min_lead_s"] == 72 * 3600


def test_intercity_pool_suggestion_even_when_pool_preferred() -> None:
    ok, rejected = allowed("INTERCITY", timedelta(hours=10), ride="POOL")
    assert ok == []
    assert rejected["CAR_INTERCITY_POOL"].details["suggested_service_code"] == "CAR_INTERCITY_PRIVATE"


def test_intercity_pool_exactly_72h_is_valid() -> None:
    """Section 72.2: exactly 72 h 00 min -> valid."""
    ok, _ = allowed("INTERCITY", timedelta(hours=72))
    assert ok == ["CAR_INTERCITY_PRIVATE", "CAR_INTERCITY_POOL"]


def test_intercity_7_day_upper_bound() -> None:
    ok_at, _ = allowed("INTERCITY", timedelta(days=7))
    ok_after, rejected = allowed("INTERCITY", timedelta(days=7, seconds=1))
    assert ok_at == ["CAR_INTERCITY_PRIVATE", "CAR_INTERCITY_POOL"]
    assert ok_after == []
    assert "suggested_service_code" not in rejected["CAR_INTERCITY_POOL"].details


def test_intercity_private_now_allowed_pool_not() -> None:
    ok, rejected = allowed("INTERCITY", timedelta(0))
    assert ok == ["CAR_INTERCITY_PRIVATE"]
    assert rejected["CAR_INTERCITY_POOL"].code == "LEAD_TIME_OUT_OF_WINDOW"


@pytest.mark.parametrize(
    "vehicle,ride,expected",
    [
        ("BIKE", "ANY", ["BIKE_URBAN"]),
        ("CAR", "ANY", ["CAR_URBAN_PRIVATE", "CAR_URBAN_POOL"]),
        ("ANY", "PRIVATE", ["BIKE_URBAN", "CAR_URBAN_PRIVATE"]),
        ("ANY", "POOL", ["CAR_URBAN_POOL"]),
        ("BIKE", "POOL", []),
    ],
)
def test_preference_filters(vehicle: str, ride: str, expected: list[str]) -> None:
    ok, _ = allowed("URBAN", timedelta(0), vehicle=vehicle, ride=ride)
    assert ok == expected
