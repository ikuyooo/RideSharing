"""driver module tables (Revision 9, Section 54).

`driver_profiles`, `vehicles`: columns per Section 56.1 (items 1-2).
`driver_locations`: not specified in 56.1; minimal structure because 56.2
requires `idx_driver_locations_geom` (GIST).
`driver_reliability_stats`: not created yet (no columns specified, no dependency).
"""

import uuid
from datetime import datetime
from typing import Any

from geoalchemy2 import Geometry
from sqlalchemy import (
    Boolean,
    CheckConstraint,
    DateTime,
    Float,
    ForeignKey,
    Index,
    Integer,
    String,
    func,
    text,
)
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base
from app.db.types import in_check

KYC_STATUSES = ("NONE", "PENDING", "VERIFIED", "REJECTED")  # Section 81
VEHICLE_TYPES = ("BIKE", "CAR4")


class DriverProfile(Base):
    __tablename__ = "driver_profiles"

    # --- Section 56.1 item 2 -------------------------------------------------
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), primary_key=True
    )
    kyc_status: Mapped[str] = mapped_column(String(16), nullable=False, server_default="NONE")
    accepts_urban: Mapped[bool] = mapped_column(Boolean, nullable=False, server_default=text("false"))
    pool_enabled: Mapped[bool] = mapped_column(Boolean, nullable=False, server_default=text("false"))
    accepts_intercity: Mapped[bool] = mapped_column(Boolean, nullable=False, server_default=text("false"))
    max_additional_pickups: Mapped[int] = mapped_column(Integer, nullable=False, server_default="0")
    max_driver_detour_km: Mapped[float | None] = mapped_column(Float)
    max_driver_detour_min: Mapped[float | None] = mapped_column(Float)

    # --- TECHNICAL ADDITIONS (Section 81 KYC mock workflow) ------------------
    kyc_submission_json: Mapped[dict[str, Any] | None] = mapped_column(JSONB)
    kyc_submitted_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    kyc_reviewed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    kyc_reviewed_by: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL")
    )

    __table_args__ = (
        in_check("kyc_status", KYC_STATUSES, "kyc_status"),
        CheckConstraint("max_additional_pickups BETWEEN 0 AND 3", name="max_additional_pickups_range"),
        # TECHNICAL ADDITION: Section 81 says POOL and intercity are locked until
        # VERIFIED; enforced in the service layer and again here.
        CheckConstraint(
            "kyc_status = 'VERIFIED' OR (pool_enabled = false AND accepts_intercity = false)",
            name="kyc_gates_pool_and_intercity",
        ),
    )


class Vehicle(Base):
    __tablename__ = "vehicles"

    # --- Section 56.1 item 1 -------------------------------------------------
    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, server_default=text("gen_random_uuid()")
    )
    driver_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("driver_profiles.user_id", ondelete="CASCADE"), nullable=False, index=True
    )
    vehicle_type: Mapped[str] = mapped_column(String(8), nullable=False)
    license_plate: Mapped[str] = mapped_column(String(20), nullable=False, unique=True)
    capacity: Mapped[int] = mapped_column(Integer, nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, server_default=text("true"))

    __table_args__ = (
        in_check("vehicle_type", VEHICLE_TYPES, "vehicle_type"),
        # Section 56.1: capacity (BIKE = 1, CAR4 = 4); D-04.
        CheckConstraint(
            "(vehicle_type = 'BIKE' AND capacity = 1) OR (vehicle_type = 'CAR4' AND capacity = 4)",
            name="capacity_matches_type",
        ),
    )


class DriverLocation(Base):
    __tablename__ = "driver_locations"

    driver_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("driver_profiles.user_id", ondelete="CASCADE"), primary_key=True
    )
    geom: Mapped[Any] = mapped_column(Geometry("POINT", srid=4326, spatial_index=False), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )

    __table_args__ = (Index("idx_driver_locations_geom", geom, postgresql_using="gist"),)
