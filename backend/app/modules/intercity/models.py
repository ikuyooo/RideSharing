"""intercity module tables (Revision 9, Section 54). Schema only in Phase 1;
intercity logic is Phase 5. `scheduled_trips`: 56.1 item 8; `seat_bookings`:
56.1 item 9. `trip_topup_offers`, `intercity_waitlist`: not created yet."""

import uuid
from datetime import datetime
from typing import Any

from geoalchemy2 import Geometry
from sqlalchemy import (
    BigInteger,
    CheckConstraint,
    DateTime,
    Float,
    ForeignKey,
    Index,
    Integer,
    String,
    text,
)
from sqlalchemy.dialects.postgresql import ARRAY, UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base
from app.db.types import in_check

SCHEDULED_TRIP_STATUSES = (
    "PUBLISHED",
    "OPEN_FOR_BOOKING",
    "BOOKING_CLOSED",
    "MERGE_PENDING_CONFIRMATION",
    "CONFIRMED",
    "TOPUP_OFFERED",
    "CONFIRMED_TOPUP",
    "UNDER_MIN_DRIVER_DECISION",
    "CONFIRMED_UNDER_MIN",
    "MERGED",
    "CANCELLED_LOW_DEMAND",
    "PICKUP_ORDER_FIXED",
    "DEPARTED",
    "COMPLETED",
)


class ScheduledTrip(Base):
    __tablename__ = "scheduled_trips"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, server_default=text("gen_random_uuid()")
    )
    driver_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("driver_profiles.user_id"), nullable=False, index=True
    )
    vehicle_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("vehicles.id"), nullable=False)
    corridor_id: Mapped[str] = mapped_column(String(64), nullable=False)
    departure_time: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    departure_flex_min: Mapped[int] = mapped_column(Integer, nullable=False, server_default="30")
    seats_total: Mapped[int] = mapped_column(Integer, nullable=False, server_default="4")
    seats_booked: Mapped[int] = mapped_column(Integer, nullable=False, server_default="0")
    min_seats_ref: Mapped[int] = mapped_column(Integer, nullable=False, server_default="3")
    min_seats_to_run: Mapped[int] = mapped_column(Integer, nullable=False, server_default="3")
    seat_reference_vnd: Mapped[int] = mapped_column(BigInteger, nullable=False)
    seat_price_vnd: Mapped[int] = mapped_column(BigInteger, nullable=False)
    pickup_zone_ids: Mapped[list[int] | None] = mapped_column(ARRAY(Integer))
    dropoff_zone_ids: Mapped[list[int] | None] = mapped_column(ARRAY(Integer))
    status: Mapped[str] = mapped_column(String(32), nullable=False, server_default="PUBLISHED")
    merged_into_trip_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("scheduled_trips.id")
    )
    plan_version: Mapped[int] = mapped_column(Integer, nullable=False, server_default="1")

    __table_args__ = (
        in_check("status", SCHEDULED_TRIP_STATUSES, "status"),
        # Section 56.2 (verbatim).
        CheckConstraint(
            "seats_booked >= 0 AND seats_booked <= seats_total AND seats_total <= 4",
            name="seats_within_capacity",
        ),
        CheckConstraint("min_seats_to_run IN (2, 3) AND min_seats_ref = 3", name="min_seats_rules"),
        CheckConstraint(
            "seat_price_vnd >= seat_reference_vnd * 9 / 10 AND seat_price_vnd <= seat_reference_vnd * 11 / 10",
            name="seat_price_band",
        ),
        Index(
            "idx_scheduled_trips_search",
            "corridor_id",
            "departure_time",
            postgresql_where=text("status = 'OPEN_FOR_BOOKING'"),
        ),
    )


class SeatBooking(Base):
    __tablename__ = "seat_bookings"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, server_default=text("gen_random_uuid()")
    )
    scheduled_trip_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("scheduled_trips.id"), nullable=False, index=True
    )
    booking_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("bookings.id"), nullable=False, unique=True
    )
    seat_count: Mapped[int | None] = mapped_column(Integer)
    pickup_geom: Mapped[Any] = mapped_column(Geometry("POINT", srid=4326, spatial_index=False))
    dropoff_geom: Mapped[Any] = mapped_column(Geometry("POINT", srid=4326, spatial_index=False))
    extra_pickup_km: Mapped[float | None] = mapped_column(Float)
    extra_dropoff_km: Mapped[float | None] = mapped_column(Float)
    door_surcharge_vnd: Mapped[int | None] = mapped_column(BigInteger)
    pickup_order: Mapped[int | None] = mapped_column(Integer)
    dropoff_order: Mapped[int | None] = mapped_column(Integer)
    planned_pickup_time: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
