"""pooling module tables (Revision 9, Section 54). Schema only in Phase 1;
pooling logic is Phase 2 (Section 79).

`ride_plans`: Section 56.1 item 4. `ride_participants`: Section 56.1 item 7.
`ride_stops`: listed in Section 54 without columns - Phase 2 TECHNICAL ADDITION,
the stop chain S_0..S_k that the Section 36 insertion works on.
"""

import uuid
from datetime import datetime
from decimal import Decimal
from typing import Any

from geoalchemy2 import Geometry
from sqlalchemy import (
    BigInteger,
    Boolean,
    CheckConstraint,
    DateTime,
    Float,
    ForeignKey,
    Integer,
    Numeric,
    String,
    UniqueConstraint,
    text,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base
from app.db.types import SERVICE_CODES, in_check

PLAN_STATUSES = (
    "PLAN_CREATED",
    "PLAN_OPEN_SEARCHING",
    "PLAN_CLOSED_TO_NEW",
    "PLAN_COMPLETED",
    "PLAN_ABORTED",
)


class RidePlan(Base):
    __tablename__ = "ride_plans"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, server_default=text("gen_random_uuid()")
    )
    driver_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("driver_profiles.user_id"), nullable=False, index=True
    )
    vehicle_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("vehicles.id"), nullable=False
    )
    service_code: Mapped[str] = mapped_column(String(32), nullable=False)
    status: Mapped[str] = mapped_column(String(32), nullable=False, server_default="PLAN_CREATED")
    completed_stop_index: Mapped[int] = mapped_column(Integer, nullable=False, server_default="-1")
    total_distance_km: Mapped[float | None] = mapped_column(Float)
    total_duration_min: Mapped[float | None] = mapped_column(Float)
    extra_stops_count: Mapped[int | None] = mapped_column(Integer)
    plan_fare_vnd: Mapped[int | None] = mapped_column(BigInteger)
    driver_hourly_rate_vnd: Mapped[int | None] = mapped_column(BigInteger)
    plan_version: Mapped[int] = mapped_column(Integer, nullable=False, server_default="1")

    __table_args__ = (
        in_check("service_code", SERVICE_CODES, "service_code"),
        in_check("status", PLAN_STATUSES, "status"),
    )


class RideParticipant(Base):
    __tablename__ = "ride_participants"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, server_default=text("gen_random_uuid()")
    )
    ride_plan_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("ride_plans.id"), nullable=False, index=True
    )
    booking_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("bookings.id"), nullable=False, unique=True
    )
    seat_count: Mapped[int | None] = mapped_column(Integer)
    private_fare_vnd: Mapped[int | None] = mapped_column(BigInteger)
    effective_private_fare_vnd: Mapped[int | None] = mapped_column(BigInteger)
    floor_fare_vnd: Mapped[int | None] = mapped_column(BigInteger)
    cap_fare_vnd: Mapped[int | None] = mapped_column(BigInteger)
    dynamic_cap_fare_vnd: Mapped[int | None] = mapped_column(BigInteger)
    traveled_km_before_last_replan: Mapped[float] = mapped_column(Float, nullable=False, server_default="0")
    detour_ratio: Mapped[float | None] = mapped_column(Float)
    walk_ratio: Mapped[float | None] = mapped_column(Float)
    allocation_weight: Mapped[float | None] = mapped_column(Float)
    fare_exact_vnd: Mapped[Decimal | None] = mapped_column(Numeric(12, 2))
    fare_charged_vnd: Mapped[int | None] = mapped_column(BigInteger)
    rounding_absorbed_vnd: Mapped[Decimal | None] = mapped_column(Numeric(10, 2))
    is_price_frozen: Mapped[bool] = mapped_column(Boolean, nullable=False, server_default=text("false"))
    # TECHNICAL ADDITION (Phase 2): the rider's direct trip (OSRM car) fixed at booking -
    # the reference of constraint 5 (detour) and of the default of constraint 6.
    direct_distance_m: Mapped[float | None] = mapped_column(Float)
    direct_duration_s: Mapped[float | None] = mapped_column(Float)

    __table_args__ = (
        # Section 56.2 (verbatim).
        CheckConstraint(
            "fare_exact_vnd >= floor_fare_vnd - 0.01 AND fare_exact_vnd <= cap_fare_vnd + 0.01",
            name="fare_exact_within_bounds",
        ),
        CheckConstraint(
            "fare_charged_vnd >= 0 AND fare_charged_vnd <= cap_fare_vnd",
            name="fare_charged_within_cap",
        ),
    )


STOP_KINDS = ("PICKUP", "DROPOFF")
STOP_STATUSES = ("PLANNED", "COMPLETED")


class RideStop(Base):
    """TECHNICAL ADDITION (Phase 2): one stop of a plan; seq 0..k in driving order.
    Stops with seq <= ride_plans.completed_stop_index are COMPLETED and frozen."""

    __tablename__ = "ride_stops"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, server_default=text("gen_random_uuid()")
    )
    ride_plan_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("ride_plans.id", ondelete="CASCADE"), nullable=False, index=True
    )
    seq: Mapped[int] = mapped_column(Integer, nullable=False)
    kind: Mapped[str] = mapped_column(String(8), nullable=False)
    booking_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("bookings.id"), nullable=False)
    geom: Mapped[Any] = mapped_column(Geometry("POINT", srid=4326, spatial_index=False), nullable=False)
    status: Mapped[str] = mapped_column(String(16), nullable=False, server_default="PLANNED")
    planned_eta: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))

    __table_args__ = (
        # Deferred so a re-plan can renumber the chain inside one transaction.
        UniqueConstraint("ride_plan_id", "seq", deferrable=True, initially="DEFERRED"),
        UniqueConstraint("booking_id", "kind"),
        in_check("kind", STOP_KINDS, "kind"),
        in_check("status", STOP_STATUSES, "status"),
        CheckConstraint("seq >= 0", name="seq_non_negative"),
        CheckConstraint("(status = 'COMPLETED') = (completed_at IS NOT NULL)", name="completed_has_time"),
    )
