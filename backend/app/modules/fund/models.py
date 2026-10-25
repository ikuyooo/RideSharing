"""fund module tables (Revision 9, Section 54). Schema only in Phase 1;
fund logic is Phase 3. `driver_payouts`, `fund_ledger`: Section 56.1 item 10."""

import uuid
from datetime import datetime

from sqlalchemy import BigInteger, DateTime, Float, ForeignKey, String, func, text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base
from app.db.types import in_check

FUND_ENTRY_TYPES = ("CONTRIBUTION", "GUARANTEE_PAYOUT", "CANCEL_FEE_INFLOW", "INITIAL_SEED")


class DriverPayout(Base):
    __tablename__ = "driver_payouts"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, server_default=text("gen_random_uuid()")
    )
    booking_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("bookings.id"), nullable=False, unique=True
    )
    driver_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("driver_profiles.user_id"), nullable=False, index=True
    )
    gross_fare_charged_vnd: Mapped[int | None] = mapped_column(BigInteger)
    driver_base_amount_vnd: Mapped[int | None] = mapped_column(BigInteger)
    guarantee_amount_vnd: Mapped[int] = mapped_column(BigInteger, nullable=False, server_default="0")
    total_driver_payout_vnd: Mapped[int | None] = mapped_column(BigInteger)
    commission_rate: Mapped[float | None] = mapped_column(Float)
    platform_net_amount_vnd: Mapped[int | None] = mapped_column(BigInteger)
    fund_contribution_vnd: Mapped[int] = mapped_column(BigInteger, nullable=False, server_default="0")


class FundLedgerEntry(Base):
    __tablename__ = "fund_ledger"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    entry_type: Mapped[str] = mapped_column(String(32), nullable=False)
    booking_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey("bookings.id"))
    amount_signed_vnd: Mapped[int] = mapped_column(BigInteger, nullable=False)
    balance_after_vnd: Mapped[int] = mapped_column(BigInteger, nullable=False)
    onchain_tx_hash: Mapped[str | None] = mapped_column(String)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )

    __table_args__ = (in_check("entry_type", FUND_ENTRY_TYPES, "entry_type"),)
