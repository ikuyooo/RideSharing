"""pooling module tables (Revision 9, Section 54). Schema only in Phase 1;
pooling logic is Phase 2 (Section 79).

`ride_plans`: Section 56.1 item 4. `ride_participants`: Section 56.1 item 7.
`ride_stops`: not created (no columns specified, no dependency yet).
"""

import uuid
from decimal import Decimal

from sqlalchemy import (
    BigInteger,
    Boolean,
    CheckConstraint,
    Float,
    ForeignKey,
    Integer,
    Numeric,
    String,
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
