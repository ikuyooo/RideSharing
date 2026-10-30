"""P2.2 - each hard constraint of Revision 9 Section 7: passing case, exact boundary and
violation."""

import uuid
from dataclasses import replace
from datetime import UTC, datetime, timedelta

import pytest

from app.modules.candidate.constraints import (
    EXISTING_POOL_PLAN,
    NEW_SINGLE_VEHICLE,
    DriverState,
    Evaluation,
    RiderOutcome,
    check_all,
)

NOW = datetime(2026, 10, 29, 8, 0, tzinfo=UTC)


def _driver(**kw: object) -> DriverState:
    base = dict(driver_id=uuid.uuid4(), availability="IDLE", location_age_s=10, kyc_status="VERIFIED",
                accepts_urban=True, pool_enabled=True, accepts_intercity=False, max_additional_pickups=2,
                max_driver_detour_km=3.0, max_driver_detour_min=10.0, vehicle_id=uuid.uuid4(), vehicle_type="CAR4",
                capacity=4, vehicle_active=True)
    return DriverState(**(base | kw))  # type: ignore[arg-type]


def _rider(**kw: object) -> RiderOutcome:
    base = dict(ref="new", seats=1, onboard=False, span=(1, 2), pickup_window=(NOW, NOW + timedelta(minutes=15)),
                planned_pickup=NOW + timedelta(minutes=5), planned_dropoff=NOW + timedelta(minutes=30),
                in_vehicle_s=1500.0, max_in_vehicle_s=1500.0, ride_distance_m=13000.0, direct_distance_m=10000.0,
                max_detour_ratio=0.30, latest_arrival=None, max_price_vnd=174000, budget_max_vnd=174000, walk_m=0,
                max_walk_m=0, same_gender=False, verified_gender=None)
    return RiderOutcome(**(base | kw))  # type: ignore[arg-type]


def _ev(service: str = "CAR_URBAN_POOL", source: str = NEW_SINGLE_VEHICLE, **kw: object) -> Evaluation:
    base = dict(service_code=service, source_type=source, driver=_driver(), location_stale_s=120,
                unroutable_legs=(), segment_loads=(0, 1), riders=(_rider(),), booking_time_ok=True,
                added_distance_m=3000.0, added_duration_s=600.0, added_pickups=0, total_stops=2, k_max_stops=8)
    return Evaluation(**(base | kw))  # type: ignore[arg-type]


def codes(ev: Evaluation) -> set[str]:
    return {v.code for v in check_all(ev)}


def test_boundaries_are_feasible() -> None:
    """Every threshold met with equality: detour exactly 0.30, in-vehicle exactly the
    maximum, pickup exactly at T_latest, budget exactly B_max, driver detour exactly its limit."""
    r = _rider(planned_pickup=NOW + timedelta(minutes=15))
    assert codes(_ev(riders=(r,), source=EXISTING_POOL_PLAN)) == set()


@pytest.mark.parametrize(("change", "code"), [
    ({"driver": _driver(availability="OFFLINE")}, "HC01"),
    ({"driver": _driver(availability="BUSY")}, "HC01"),                     # new vehicle must be IDLE
    ({"driver": _driver(location_age_s=121)}, "HC01"),
    ({"driver": _driver(kyc_status="PENDING")}, "HC01"),                    # POOL needs KYC VERIFIED (S7)
    ({"driver": _driver(pool_enabled=False)}, "HC01"),
    ({"driver": _driver(vehicle_type="BIKE", capacity=1)}, "HC01"),
    ({"driver": _driver(vehicle_active=False)}, "HC01"),
    ({"unroutable_legs": ("0->1",)}, "HC02"),
    ({"riders": (_rider(planned_pickup=NOW + timedelta(minutes=15, seconds=1)),)}, "HC03"),
    ({"segment_loads": (4, 5)}, "HC04"),
    ({"riders": (_rider(ride_distance_m=13001.0),)}, "HC05"),
    ({"riders": (_rider(in_vehicle_s=1500.5),)}, "HC06"),
    ({"riders": (_rider(latest_arrival=NOW + timedelta(minutes=29)),)}, "HC06"),
    ({"source_type": EXISTING_POOL_PLAN, "added_distance_m": 3001.0}, "HC07"),
    ({"source_type": EXISTING_POOL_PLAN, "added_duration_s": 601.0}, "HC07"),
    ({"source_type": EXISTING_POOL_PLAN, "driver": _driver(availability="BUSY"), "added_pickups": 3}, "HC07"),
    ({"total_stops": 9}, "HC07"),
    ({"riders": (_rider(budget_max_vnd=173999),)}, "HC08"),
    ({"booking_time_ok": False}, "HC09"),
    ({"riders": (_rider(walk_m=1),)}, "HC10"),
])
def test_each_violation(change: dict, code: str) -> None:
    assert codes(_ev(**change)) == {code}


def test_existing_plan_driver_may_be_busy_but_not_offline() -> None:
    assert codes(_ev(source=EXISTING_POOL_PLAN, driver=_driver(availability="BUSY"))) == set()


def test_detour_and_driver_limits_apply_to_the_pool_only() -> None:
    far = _rider(ride_distance_m=20000.0)
    ev = _ev(service="CAR_URBAN_PRIVATE", riders=(far,), added_distance_m=99999.0, total_stops=2,
             driver=_driver(kyc_status="NONE", pool_enabled=False))
    assert codes(ev) == set()  # PRIVATE: no HC05 / HC07, no KYC requirement


def test_same_gender_only_on_overlapping_segments() -> None:
    a = _rider(ref="A", onboard=True, span=(0, 2), pickup_window=None, planned_pickup=None, same_gender=True,
               verified_gender="F")
    overlapping = _rider(span=(1, 3), verified_gender="M")
    after = _rider(span=(2, 3), verified_gender="M")
    assert codes(_ev(riders=(a, overlapping), segment_loads=(1, 2, 1))) == {"HC11"}
    assert codes(_ev(riders=(a, after), segment_loads=(1, 1, 1))) == set()
    assert codes(_ev(riders=(a, replace(overlapping, verified_gender=None)), segment_loads=(1, 2, 1))) == {"HC11"}
    assert codes(_ev(riders=(a, replace(overlapping, verified_gender="F")), segment_loads=(1, 2, 1))) == set()
