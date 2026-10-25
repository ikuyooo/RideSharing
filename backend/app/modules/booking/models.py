"""booking module tables (Revision 9, Section 54). Schema only in Phase 1;
booking logic is Phase 4.

`bookings`: Section 56.1 item 6 (three orthogonal status axes, D-46).
`seat_holds`, `idempotency_records`: not specified in 56.1; minimal structure
because 56.2 requires `idx_active_hold_per_request` and
UNIQUE (user_id, idempotency_key). `offers`: not created yet.
"""

import uuid
from datetime import datetime

from sqlalchemy import (
    BigInteger,
    CheckConstraint,
    DateTime,
    ForeignKey,
    Index,
    Integer,
    String,
    UniqueConstraint,
    func,
    text,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base
from app.db.types import SERVICE_CODES, in_check

BOOKING_TYPES = ("NOW", "SCHEDULED")
RIDE_STATUSES = (
    "HELD",
    "CONFIRMED",
    "RIDE_STARTED",
    "COMPLETED",
    "EXPIRED",
    "CANCELLED_BY_PASSENGER",
    "CANCELLED_BY_DRIVER",
    "CANCELLED_BY_SYSTEM",
    "NO_SHOW",
)
PRICE_STATUSES = (
    "QUOTED",
    "FIXED_LOCKED",
    "POOL_SEARCHING",
    "MATCHED_LOCKED",
    "UNMATCHED_LOCKED",
    "MERGED_REDUCED_LOCKED",
    "TOPUP_LOCKED",
)
ESCROW_STATUSES = (
    "NONE",
    "DEPOSIT_PENDING",
    "DEPOSITED",
    "LOCKED",
    "TOPPED_UP",
    "RELEASED",
    "REFUNDED",
    "ESCROW_FAILED",
    "DISPUTED",
    "RESOLVED",
)
UNMATCHED_CAUSES = (
    "NONE",
    "NO_COMPATIBLE",
    "DRIVER_DECLINED",
    "CORIDER_CANCELLED_EARLY",
    "CORIDER_CANCELLED_LATE",
    "PASSENGER_REJECTED_POOL",
)


class Booking(Base):
    __tablename__ = "bookings"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, server_default=text("gen_random_uuid()")
    )
    request_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("trip_requests.id"), nullable=False, index=True
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id"), nullable=False, index=True
    )
    driver_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("driver_profiles.user_id"), index=True
    )
    service_code: Mapped[str] = mapped_column(String(32), nullable=False)
    booking_type: Mapped[str] = mapped_column(String(16), nullable=False)
    seat_count: Mapped[int] = mapped_column(Integer, nullable=False, server_default="1")
    ride_plan_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey("ride_plans.id"))
    scheduled_trip_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("scheduled_trips.id")
    )
    ride_status: Mapped[str] = mapped_column(String(32), nullable=False, server_default="HELD")
    price_status: Mapped[str] = mapped_column(String(32), nullable=False, server_default="QUOTED")
    escrow_status: Mapped[str] = mapped_column(String(32), nullable=False, server_default="NONE")
    pool_quote_price_vnd: Mapped[int | None] = mapped_column(BigInteger)
    quoted_price_cap_vnd: Mapped[int | None] = mapped_column(BigInteger)
    current_estimated_price_vnd: Mapped[int | None] = mapped_column(BigInteger)
    final_price_vnd: Mapped[int | None] = mapped_column(BigInteger)
    cancellation_fee_vnd: Mapped[int] = mapped_column(BigInteger, nullable=False, server_default="0")
    pool_lock_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    unmatched_cause: Mapped[str] = mapped_column(String(32), nullable=False, server_default="NONE")
    escrow_tx_deposit: Mapped[str | None] = mapped_column(String)
    escrow_tx_lock_or_topup: Mapped[str | None] = mapped_column(String)
    escrow_tx_settle: Mapped[str | None] = mapped_column(String)

    __table_args__ = (
        in_check("service_code", SERVICE_CODES, "service_code"),
        in_check("booking_type", BOOKING_TYPES, "booking_type"),
        in_check("ride_status", RIDE_STATUSES, "ride_status"),
        in_check("price_status", PRICE_STATUSES, "price_status"),
        in_check("escrow_status", ESCROW_STATUSES, "escrow_status"),
        in_check("unmatched_cause", UNMATCHED_CAUSES, "unmatched_cause"),
        # Section 56.2 (verbatim).
        CheckConstraint(
            "final_price_vnd IS NULL OR final_price_vnd <= quoted_price_cap_vnd "
            "OR price_status = 'TOPUP_LOCKED'",
            name="final_price_within_cap",
        ),
    )


class SeatHold(Base):
    __tablename__ = "seat_holds"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, server_default=text("gen_random_uuid()")
    )
    request_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("trip_requests.id"), nullable=False
    )
    # Only 'ACTIVE' is named by Revision 9 (56.2); the full status set is
    # defined in Phase 4 (Section 41), so no CHECK on values yet.
    status: Mapped[str] = mapped_column(String(16), nullable=False)
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )

    __table_args__ = (
        # Section 56.2 (verbatim name and predicate).
        Index(
            "idx_active_hold_per_request",
            "request_id",
            unique=True,
            postgresql_where=text("status = 'ACTIVE'"),
        ),
    )


class IdempotencyRecord(Base):
    __tablename__ = "idempotency_records"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    user_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    idempotency_key: Mapped[str] = mapped_column(String(128), nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )

    __table_args__ = (
        # Section 56.2: UNIQUE (user_id, idempotency_key).
        UniqueConstraint("user_id", "idempotency_key"),
        CheckConstraint("length(idempotency_key) > 0", name="key_not_empty"),
    )
