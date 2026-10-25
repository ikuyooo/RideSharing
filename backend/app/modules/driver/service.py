"""driver service - the only code that writes `driver_profiles`, `vehicles`
and `driver_locations`.

KYC mock (Revision 9, Section 81; SHOULD S7):
  NONE/REJECTED --submit--> PENDING --admin--> VERIFIED | REJECTED
Until VERIFIED, `pool_enabled` and `accepts_intercity` stay locked (403
KYC_REQUIRED); intercity trip publishing (Phase 5) must call
`assert_kyc_verified`.
"""

import uuid
from datetime import UTC, datetime
from typing import Any

from geoalchemy2.elements import WKTElement
from sqlalchemy import select
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
