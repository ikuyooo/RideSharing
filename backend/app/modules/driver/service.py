"""driver service - the only code that writes `driver_profiles`, `vehicles`
and `driver_locations`.

KYC mock (Revision 9, Section 81; SHOULD S7):
  NONE/REJECTED --submit--> PENDING --admin--> VERIFIED | REJECTED
Until VERIFIED, `pool_enabled` and `accepts_intercity` stay locked (403
KYC_REQUIRED); intercity trip publishing (Phase 5) must call
`assert_kyc_verified`.
"""

import math
import uuid
from dataclasses import dataclass
from datetime import UTC, datetime
from typing import Any

from geoalchemy2.elements import WKTElement
from sqlalchemy import select, text
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.core.config_baseline import get_config_baseline
from app.core.errors import ApiError
from app.modules.driver.models import DriverLocation, DriverProfile, Vehicle
from app.modules.driver.schemas import DriverSettingsIn


def vehicle_capacity(vehicle_type: str) -> int:
    """Seats per vehicle type from the baseline (bike_urban/car_urban.capacity; D-04)."""
    baseline = get_config_baseline()
    return int(baseline["bike_urban"]["capacity"] if vehicle_type == "BIKE" else baseline["car_urban"]["capacity"])


def ensure_profile(session: Session, user_id: uuid.UUID) -> DriverProfile:
    profile = session.get(DriverProfile, user_id)
    if profile is None:
        session.execute(insert(DriverProfile).values(user_id=user_id).on_conflict_do_nothing())
        session.commit()
        profile = session.get(DriverProfile, user_id)
    assert profile is not None
    return profile


def list_vehicles(session: Session, driver_id: uuid.UUID) -> list[Vehicle]:
    return list(session.scalars(select(Vehicle).where(Vehicle.driver_id == driver_id).order_by(Vehicle.license_plate)))


def add_vehicle(session: Session, driver_id: uuid.UUID, vehicle_type: str, license_plate: str) -> Vehicle:
    ensure_profile(session, driver_id)
    vehicle = Vehicle(
        driver_id=driver_id,
        vehicle_type=vehicle_type,
        license_plate=license_plate.upper().strip(),
        capacity=vehicle_capacity(vehicle_type),
    )
    session.add(vehicle)
    try:
        session.commit()
    except IntegrityError as exc:
        session.rollback()
        if "uq_vehicles_license_plate" in str(exc.orig):
            raise ApiError(409, "LICENSE_PLATE_TAKEN", "This licence plate is already registered") from exc
        raise
    return vehicle


def submit_kyc(session: Session, driver_id: uuid.UUID, submission: dict[str, Any]) -> DriverProfile:
    profile = ensure_profile(session, driver_id)
    if profile.kyc_status not in ("NONE", "REJECTED"):
        raise ApiError(409, "KYC_ALREADY_SUBMITTED", f"KYC status is {profile.kyc_status}")
    profile.kyc_status = "PENDING"
    profile.kyc_submission_json = submission | {"mock": True}
    profile.kyc_submitted_at = datetime.now(UTC)
    profile.kyc_reviewed_at = None
    profile.kyc_reviewed_by = None
    session.commit()
    return profile


def review_kyc(session: Session, driver_id: uuid.UUID, decision: str, admin_id: uuid.UUID) -> DriverProfile:
    profile = session.get(DriverProfile, driver_id, with_for_update=True)
    if profile is None:
        raise ApiError(404, "NOT_FOUND", "Driver not found")
    if profile.kyc_status != "PENDING":
        raise ApiError(409, "KYC_NOT_PENDING", f"KYC status is {profile.kyc_status}")
    profile.kyc_status = decision
    profile.kyc_reviewed_at = datetime.now(UTC)
    profile.kyc_reviewed_by = admin_id
    if decision != "VERIFIED":
        profile.pool_enabled = False
        profile.accepts_intercity = False
    session.commit()
    return profile


def assert_kyc_verified(profile: DriverProfile) -> None:
    if profile.kyc_status != "VERIFIED":
        raise ApiError(403, "KYC_REQUIRED", "Driver KYC must be VERIFIED for this action")


def update_settings(session: Session, driver_id: uuid.UUID, body: DriverSettingsIn) -> DriverProfile:
    profile = ensure_profile(session, driver_id)
    changes = body.model_dump(exclude_unset=True)
    if changes.get("pool_enabled") or changes.get("accepts_intercity"):
        # Section 81 (KYC gate) and Section 3 (pool / intercity are taxi modes).
        assert_kyc_verified(profile)
        has_car = any(v.is_active and v.vehicle_type == "CAR4" for v in list_vehicles(session, driver_id))
        if not has_car:
            raise ApiError(422, "CAR4_VEHICLE_REQUIRED", "Pool and intercity modes need an active CAR4 vehicle")
    for field, value in changes.items():
        setattr(profile, field, value)
    session.commit()
    return profile


def update_location(session: Session, driver_id: uuid.UUID, lat: float, lon: float) -> None:
    ensure_profile(session, driver_id)
    point = WKTElement(f"POINT({lon} {lat})", srid=4326)
    stmt = insert(DriverLocation).values(driver_id=driver_id, geom=point)
    stmt = stmt.on_conflict_do_update(
        index_elements=[DriverLocation.driver_id], set_={"geom": point, "updated_at": datetime.now(UTC)}
    )
    session.execute(stmt)
    session.commit()


# --- Phase 2: availability and candidate look-ups (hard constraint 1, Section 35) ---

@dataclass(frozen=True)
class DriverCandidate:
    """Read-only snapshot used by candidate generation."""

    driver_id: uuid.UUID
    lon: float
    lat: float
    distance_m: float
    availability: str
    location_age_s: float
    kyc_status: str
    accepts_urban: bool
    pool_enabled: bool
    accepts_intercity: bool
    max_additional_pickups: int
    max_driver_detour_km: float | None
    max_driver_detour_min: float | None
    vehicle_id: uuid.UUID | None
    vehicle_type: str | None
    capacity: int
    vehicle_active: bool


def set_availability(session: Session, driver_id: uuid.UUID, availability: str, vehicle_id: uuid.UUID | None) -> None:
    """Driver toggles OFFLINE / IDLE. BUSY is set by the ride lifecycle (Phase 4), so a
    BUSY driver cannot toggle here."""
    row = session.get(DriverLocation, driver_id, with_for_update=True)
    if row is None:
        raise ApiError(409, "LOCATION_REQUIRED", "Send the current location before going online")
    if row.availability == "BUSY":
        raise ApiError(409, "DRIVER_BUSY", "Availability cannot change during a ride")
    if availability == "IDLE":
        vehicle = session.get(Vehicle, vehicle_id) if vehicle_id else None
        if vehicle is None or vehicle.driver_id != driver_id or not vehicle.is_active:
            raise ApiError(422, "VEHICLE_REQUIRED", "Choose one of your active vehicles to go online")
        row.active_vehicle_id = vehicle.id
    row.availability = availability
    session.commit()


_CANDIDATE_COLUMNS = """
    dl.driver_id, ST_X(dl.geom) AS lon, ST_Y(dl.geom) AS lat,
    ST_Distance(dl.geom::geography, ST_SetSRID(ST_MakePoint(:lon, :lat), 4326)::geography) AS distance_m,
    dl.availability, EXTRACT(EPOCH FROM (:now - dl.updated_at)) AS location_age_s,
    dp.kyc_status, dp.accepts_urban, dp.pool_enabled, dp.accepts_intercity, dp.max_additional_pickups,
    dp.max_driver_detour_km, dp.max_driver_detour_min,
    v.id AS vehicle_id, v.vehicle_type, COALESCE(v.capacity, 0) AS capacity, COALESCE(v.is_active, false) AS vehicle_active
"""


def nearby_idle_drivers(session: Session, lon: float, lat: float, radius_m: float, vehicle_type: str, limit: int,
                        now: datetime, fresh_s: float, pool_only: bool = False) -> list[DriverCandidate]:
    """Section 35.1 steps 1-3: online IDLE drivers of the vehicle type within radius_m
    (PostGIS ST_DWithin on geography), nearest first, at most `limit`. The `&&`
    bounding box lets the GIST index on the geometry column prune first."""
    deg = radius_m / (111_320.0 * max(0.1, math.cos(math.radians(lat))))
    pool = "AND dp.pool_enabled AND dp.kyc_status = 'VERIFIED'" if pool_only else ""
    rows = session.execute(text(f"""
        SELECT {_CANDIDATE_COLUMNS}
        FROM driver_locations dl
        JOIN driver_profiles dp ON dp.user_id = dl.driver_id
        JOIN vehicles v ON v.id = dl.active_vehicle_id
        WHERE dl.availability = 'IDLE' AND dl.updated_at >= :now - make_interval(secs => :fresh_s)
          AND v.vehicle_type = :vt AND v.is_active AND dp.accepts_urban {pool}
          AND dl.geom && ST_Expand(ST_SetSRID(ST_MakePoint(:lon, :lat), 4326), :deg)
          AND ST_DWithin(dl.geom::geography, ST_SetSRID(ST_MakePoint(:lon, :lat), 4326)::geography, :r)
        ORDER BY distance_m
        LIMIT :n"""), {"lon": lon, "lat": lat, "now": now, "fresh_s": fresh_s, "vt": vehicle_type, "deg": deg,
                       "r": radius_m, "n": limit}).mappings().all()
    return [DriverCandidate(**dict(r)) for r in rows]


def driver_snapshots(session: Session, driver_ids: list[uuid.UUID], lon: float, lat: float,
                     now: datetime) -> dict[uuid.UUID, DriverCandidate]:
    """Snapshots of given drivers (the drivers of open pool plans), whatever their state."""
    if not driver_ids:
        return {}
    rows = session.execute(text(f"""
        SELECT {_CANDIDATE_COLUMNS}
        FROM driver_locations dl
        JOIN driver_profiles dp ON dp.user_id = dl.driver_id
        LEFT JOIN vehicles v ON v.id = dl.active_vehicle_id
        WHERE dl.driver_id = ANY(:ids)"""), {"ids": driver_ids, "lon": lon, "lat": lat, "now": now}).mappings().all()
    return {r["driver_id"]: DriverCandidate(**dict(r)) for r in rows}
