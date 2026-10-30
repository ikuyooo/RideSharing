"""The 11 hard constraints of Revision 9 Section 7 ([ACCEPTED] D-02, D-04, D-05, D-24).

Every candidate - a new single vehicle or an insertion into an open pool plan - is
evaluated into an immutable `Evaluation` (the driver, the stop chain's legs, the seat
load of every segment and the outcome for EVERY rider of the plan, not only the new
one) and passed to `check_all`. A candidate exists only if `check_all` returns no
violation. Nothing here is a score: ranking / AI layers receive only feasible
candidates and never these thresholds (Section 43, principle 1).

Units: metres, seconds, VND, timezone-aware datetimes.
"""

import uuid
from collections.abc import Callable
from dataclasses import dataclass, field
from datetime import datetime

POOL = "CAR_URBAN_POOL"
KYC_REQUIRED = frozenset({"CAR_URBAN_POOL", "CAR_INTERCITY_PRIVATE", "CAR_INTERCITY_POOL"})
VEHICLE_FOR = {"BIKE_URBAN": "BIKE", "CAR_URBAN_PRIVATE": "CAR4", "CAR_URBAN_POOL": "CAR4",
               "CAR_INTERCITY_PRIVATE": "CAR4", "CAR_INTERCITY_POOL": "CAR4"}
NEW_SINGLE_VEHICLE = "NEW_SINGLE_VEHICLE"
EXISTING_POOL_PLAN = "EXISTING_POOL_PLAN"
EPS_S = 1e-6


@dataclass(frozen=True)
class Violation:
    code: str      # HC01 .. HC11
    subject: str   # "driver", "plan" or a rider reference
    detail: str


@dataclass(frozen=True)
class DriverState:
    driver_id: uuid.UUID
    availability: str               # OFFLINE | IDLE | BUSY
    location_age_s: float
    kyc_status: str
    accepts_urban: bool
    pool_enabled: bool
    accepts_intercity: bool
    max_additional_pickups: int
    max_driver_detour_km: float | None
    max_driver_detour_min: float | None
    vehicle_id: uuid.UUID | None
    vehicle_type: str | None        # BIKE | CAR4
    capacity: int
    vehicle_active: bool


@dataclass(frozen=True)
class RiderOutcome:
    """One booking of the evaluated stop chain."""

    ref: str                                   # "new" or the booking id
    seats: int
    onboard: bool                              # picked up before the evaluation (running vehicle)
    span: tuple[int, int]                      # segments [first, end) the rider occupies
    pickup_window: tuple[datetime, datetime] | None  # None when already onboard
    planned_pickup: datetime | None            # None when already onboard
    planned_dropoff: datetime
    in_vehicle_s: float
    max_in_vehicle_s: float
    ride_distance_m: float                     # traveled so far + remaining in the chain
    direct_distance_m: float
    max_detour_ratio: float
    latest_arrival: datetime | None
    max_price_vnd: int | None                  # fixed fare, or Unmatched_i for the pool
    budget_max_vnd: int | None
    walk_m: int
    max_walk_m: int
    same_gender: bool
    verified_gender: str | None                # None when not verified (self-declared never counts)


@dataclass(frozen=True)
class Evaluation:
    service_code: str
    source_type: str                           # NEW_SINGLE_VEHICLE | EXISTING_POOL_PLAN
    driver: DriverState
    location_stale_s: float
    unroutable_legs: tuple[str, ...]           # legs of the chain without a road (profile-specific)
    segment_loads: tuple[int, ...]             # seats in use on each segment of the chain
    riders: tuple[RiderOutcome, ...]
    booking_time_ok: bool
    booking_time_detail: str = ""
    added_distance_m: float = 0.0
    added_duration_s: float = 0.0
    added_pickups: int = 0                     # bookings in the plan beyond the first
    total_stops: int = 2
    k_max_stops: int = 8
    extra: dict[str, object] = field(default_factory=dict, compare=False)


def hc01_vehicle_and_driver(ev: Evaluation) -> list[Violation]:
    d, out = ev.driver, []
    if d.availability == "OFFLINE" or d.location_age_s > ev.location_stale_s:
        out.append(Violation("HC01", "driver", f"offline or stale location ({d.location_age_s:.0f} s)"))
    if ev.source_type == NEW_SINGLE_VEHICLE and d.availability != "IDLE":
        out.append(Violation("HC01", "driver", f"not IDLE ({d.availability})"))
    if d.vehicle_id is None or not d.vehicle_active or d.vehicle_type != VEHICLE_FOR[ev.service_code]:
        out.append(Violation("HC01", "driver", f"vehicle {d.vehicle_type} inactive or wrong type for {ev.service_code}"))
    if ev.service_code.startswith("CAR_URBAN") or ev.service_code == "BIKE_URBAN":
        if not d.accepts_urban:
            out.append(Violation("HC01", "driver", "does not accept urban trips"))
    else:
        if not d.accepts_intercity:
            out.append(Violation("HC01", "driver", "does not accept intercity trips"))
    if ev.service_code == POOL and not d.pool_enabled:
        out.append(Violation("HC01", "driver", "pool not enabled"))
    if ev.service_code in KYC_REQUIRED and d.kyc_status != "VERIFIED":
        out.append(Violation("HC01", "driver", f"KYC {d.kyc_status}"))
    return out


def hc02_route_exists(ev: Evaluation) -> list[Violation]:
    return [Violation("HC02", "plan", f"no road for leg {leg}") for leg in ev.unroutable_legs]


def hc03_pickup_window(ev: Evaluation) -> list[Violation]:
    out = []
    for r in ev.riders:
        if r.onboard:
            continue
        lo, hi = r.pickup_window  # type: ignore[misc]
        if r.planned_pickup is None or not (lo <= r.planned_pickup <= hi):
            out.append(Violation("HC03", r.ref, f"pickup {r.planned_pickup} outside [{lo}, {hi}]"))
    return out


def hc04_segment_capacity(ev: Evaluation) -> list[Violation]:
    return [Violation("HC04", "plan", f"segment {i}: {load} seats > capacity {ev.driver.capacity}")
            for i, load in enumerate(ev.segment_loads) if load > ev.driver.capacity]


def hc05_passenger_detour(ev: Evaluation) -> list[Violation]:
    if ev.service_code != POOL:
        return []
    out = []
    for r in ev.riders:
        detour = (r.ride_distance_m - r.direct_distance_m) / r.direct_distance_m if r.direct_distance_m > 0 else 0.0
        if detour > r.max_detour_ratio + 1e-9:
            out.append(Violation("HC05", r.ref, f"detour {detour:.4f} > {r.max_detour_ratio}"))
    return out


def hc06_in_vehicle_time(ev: Evaluation) -> list[Violation]:
    out = []
    for r in ev.riders:
        if r.in_vehicle_s > r.max_in_vehicle_s + EPS_S:
            out.append(Violation("HC06", r.ref, f"in-vehicle {r.in_vehicle_s:.0f} s > {r.max_in_vehicle_s:.0f} s"))
        if r.latest_arrival is not None and r.planned_dropoff > r.latest_arrival:
            out.append(Violation("HC06", r.ref, f"dropoff {r.planned_dropoff} after latest_arrival {r.latest_arrival}"))
    return out


def hc07_driver_limits(ev: Evaluation) -> list[Violation]:
    if ev.service_code != POOL:
        return []
    d, out = ev.driver, []
    if d.max_driver_detour_km is not None and ev.added_distance_m > d.max_driver_detour_km * 1000 + 1e-6:
        out.append(Violation("HC07", "driver", f"extra {ev.added_distance_m:.0f} m > {d.max_driver_detour_km} km"))
    if d.max_driver_detour_min is not None and ev.added_duration_s > d.max_driver_detour_min * 60 + EPS_S:
        out.append(Violation("HC07", "driver", f"extra {ev.added_duration_s:.0f} s > {d.max_driver_detour_min} min"))
    if ev.added_pickups > d.max_additional_pickups:
        out.append(Violation("HC07", "driver", f"{ev.added_pickups} additional pickups > {d.max_additional_pickups}"))
    if ev.total_stops > ev.k_max_stops:
        out.append(Violation("HC07", "plan", f"{ev.total_stops} stops > k_max_stops {ev.k_max_stops}"))
    return out


def hc08_budget_cap(ev: Evaluation) -> list[Violation]:
    out = []
    for r in ev.riders:
        if r.budget_max_vnd is None:
            continue
        if r.max_price_vnd is None or r.max_price_vnd > r.budget_max_vnd:
            out.append(Violation("HC08", r.ref, f"max price {r.max_price_vnd} > B_max {r.budget_max_vnd}"))
    return out


def hc09_booking_time(ev: Evaluation) -> list[Violation]:
    return [] if ev.booking_time_ok else [Violation("HC09", "new", ev.booking_time_detail or "booking time rule")]


def hc10_walk(ev: Evaluation) -> list[Violation]:
    return [Violation("HC10", r.ref, f"walk {r.walk_m} m > {r.max_walk_m} m") for r in ev.riders if r.walk_m > r.max_walk_m]


def hc11_same_gender(ev: Evaluation) -> list[Violation]:
    out = []
    riders = ev.riders
    for a in riders:
        if not a.same_gender:
            continue
        for b in riders:
            if b is a or b.span[0] >= a.span[1] or a.span[0] >= b.span[1]:
                continue  # no overlapping segment
            if a.verified_gender is None or b.verified_gender is None or a.verified_gender != b.verified_gender:
                out.append(Violation("HC11", a.ref, f"co-rides with {b.ref} without a verified same gender"))
    return out


HARD_CONSTRAINTS: dict[str, Callable[[Evaluation], list[Violation]]] = {
    "HC01": hc01_vehicle_and_driver,
    "HC02": hc02_route_exists,
    "HC03": hc03_pickup_window,
    "HC04": hc04_segment_capacity,
    "HC05": hc05_passenger_detour,
    "HC06": hc06_in_vehicle_time,
    "HC07": hc07_driver_limits,
    "HC08": hc08_budget_cap,
    "HC09": hc09_booking_time,
    "HC10": hc10_walk,
    "HC11": hc11_same_gender,
}


def check_all(ev: Evaluation) -> list[Violation]:
    """All 11 constraints, for every rider of the chain. Empty list = feasible."""
    return [v for check in HARD_CONSTRAINTS.values() for v in check(ev)]
