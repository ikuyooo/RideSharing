"""trip module tables (Revision 9, Section 54).

`trip_requests`: columns per Section 56.1 item 3 (+ marked technical additions).
`service_areas`: not specified in 56.1; minimal structure for Section 2.3 and
the GIST index `idx_service_areas_geom` required by 56.2.
`recurring_trip_templates` (COULD C4): not created; `recurring_template_id` is
therefore a plain UUID without FK for now.
"""

import uuid
from datetime import datetime
from typing import Any

from geoalchemy2 import Geometry
from sqlalchemy import (
    BigInteger,
    Boolean,
    CheckConstraint,
    DateTime,
    Float,
    ForeignKey,
    Index,
    Integer,
    String,
    Text,
    UniqueConstraint,
    func,
    text,
)
from sqlalchemy.dialects.postgresql import ARRAY, JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base
from app.db.types import in_check

MODES = ("URBAN", "INTERCITY")
VEHICLE_PREFERENCES = ("BIKE", "CAR", "ANY")
RIDE_PREFERENCES = ("PRIVATE", "POOL", "ANY")
BOOKING_TYPES = ("NOW", "SCHEDULED")
AREA_TYPES = ("URBAN", "TOTAL")  # urban_service_area / total_service_area (Section 2.3)
# CANDIDATE until the owner approves a concrete geometry (P1-D1 / P1-D3).
AREA_STATUSES = ("CANDIDATE", "APPROVED", "RETIRED")


class TripRequest(Base):
    __tablename__ = "trip_requests"

    # --- Section 56.1 item 3 -------------------------------------------------
    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, server_default=text("gen_random_uuid()")
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id"), nullable=False, index=True
    )
    mode: Mapped[str] = mapped_column(String(16), nullable=False)
    vehicle_preference: Mapped[str] = mapped_column(String(8), nullable=False)
    ride_preference: Mapped[str] = mapped_column(String(8), nullable=False)
    allowed_service_codes: Mapped[list[str]] = mapped_column(ARRAY(Text), nullable=False)
    rejection_reasons_json: Mapped[Any] = mapped_column(JSONB, nullable=False)
    booking_type: Mapped[str] = mapped_column(String(16), nullable=False)
    passenger_count: Mapped[int] = mapped_column(Integer, nullable=False)
    has_luggage: Mapped[bool] = mapped_column(Boolean, nullable=False)
    pickup_geom: Mapped[Any] = mapped_column(Geometry("POINT", srid=4326, spatial_index=False), nullable=False)
    dropoff_geom: Mapped[Any] = mapped_column(Geometry("POINT", srid=4326, spatial_index=False), nullable=False)
    pickup_zone_id: Mapped[int | None] = mapped_column(Integer)
    dropoff_zone_id: Mapped[int | None] = mapped_column(Integer)
    preferred_departure: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    earliest_departure: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    latest_departure: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    latest_arrival: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    budget_min: Mapped[int | None] = mapped_column(BigInteger)
    budget_max: Mapped[int | None] = mapped_column(BigInteger)
    max_passenger_detour_ratio: Mapped[float | None] = mapped_column(Float)
    max_in_vehicle_time_s: Mapped[int | None] = mapped_column(Integer)
    max_walk_m: Mapped[int | None] = mapped_column(Integer)
    categorical_preferences_json: Mapped[Any | None] = mapped_column(JSONB)
    recurring_template_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True))

    # --- TECHNICAL ADDITIONS (traceability of the Section 2.3 classification) -
    service_area_version: Mapped[str] = mapped_column(String(64), nullable=False)
    direct_distance_km: Mapped[float | None] = mapped_column(Float)  # OSRM car (P1-D2)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )

    __table_args__ = (
        in_check("mode", MODES, "mode"),
        in_check("vehicle_preference", VEHICLE_PREFERENCES, "vehicle_preference"),
        in_check("ride_preference", RIDE_PREFERENCES, "ride_preference"),
        in_check("booking_type", BOOKING_TYPES, "booking_type"),
        CheckConstraint("passenger_count BETWEEN 1 AND 4", name="passenger_count_range"),
    )


class ServiceArea(Base):
    __tablename__ = "service_areas"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    area_type: Mapped[str] = mapped_column(String(8), nullable=False)
    service_area_version: Mapped[str] = mapped_column(String(64), nullable=False)
    status: Mapped[str] = mapped_column(String(16), nullable=False, server_default="CANDIDATE")
    geom: Mapped[Any] = mapped_column(
        Geometry("MULTIPOLYGON", srid=4326, spatial_index=False), nullable=False
    )
    source_json: Mapped[Any] = mapped_column(JSONB, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )
    approved_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    approval_reference: Mapped[str | None] = mapped_column(Text)

    __table_args__ = (
        in_check("area_type", AREA_TYPES, "area_type"),
        in_check("status", AREA_STATUSES, "status"),
        UniqueConstraint("area_type", "service_area_version"),
        CheckConstraint("status <> 'APPROVED' OR approved_at IS NOT NULL", name="approved_has_timestamp"),
        Index("idx_service_areas_geom", geom, postgresql_using="gist"),
    )
