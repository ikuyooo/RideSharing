"""fund module tables (Revision 9, Section 54). `driver_payouts`, `fund_ledger`: Section 56.1
item 10. Phase 3 TECHNICAL ADDITIONS (migration 0006): payout kind, pricing / pool policy versions and
cause on every payout; versions, plan and reason on every ledger entry; integrity CHECKs (split adds up,
sign by entry type, balance never negative, one entry per booking and type, one seed). Triggers make
both tables append-only and enforce the ledger balance chain (fund_ledger.onchain_tx_hash may be filled
once, by Phase 9)."""

import uuid
from datetime import datetime

from sqlalchemy import BigInteger, CheckConstraint, DateTime, Float, ForeignKey, Index, String, func, text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base
from app.db.types import in_check

FUND_ENTRY_TYPES = ("CONTRIBUTION", "GUARANTEE_PAYOUT", "CANCEL_FEE_INFLOW", "INITIAL_SEED")
PAYOUT_KINDS = ("FIXED", "POOL_MATCHED", "POOL_UNMATCHED", "INTERCITY_SEAT", "INTERCITY_TOPUP",
                "INTERCITY_UNDER_MIN", "CANCELLATION_FEE")


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
    # --- TECHNICAL ADDITIONS (Phase 3) ---------------------------------------
    payout_kind: Mapped[str] = mapped_column(String(24), nullable=False)
    pricing_version: Mapped[str] = mapped_column(String(64), nullable=False)
    pool_policy_version: Mapped[str | None] = mapped_column(String(64))
    unmatched_cause: Mapped[str] = mapped_column(String(32), nullable=False, server_default="NONE")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, server_default=func.now())

    __table_args__ = (
        in_check("payout_kind", PAYOUT_KINDS, "payout_kind"),
        CheckConstraint("gross_fare_charged_vnd >= 0 AND driver_base_amount_vnd >= 0 AND guarantee_amount_vnd >= 0 "
                        "AND platform_net_amount_vnd >= 0 AND fund_contribution_vnd >= 0",
                        name="payout_amounts_non_negative"),
        CheckConstraint("total_driver_payout_vnd = driver_base_amount_vnd + guarantee_amount_vnd",
                        name="payout_total_is_base_plus_guarantee"),
        CheckConstraint("gross_fare_charged_vnd = driver_base_amount_vnd + platform_net_amount_vnd "
                        "+ fund_contribution_vnd", name="payout_gross_is_split_exactly"),
    )


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
    # --- TECHNICAL ADDITIONS (Phase 3) ---------------------------------------
    pricing_version: Mapped[str | None] = mapped_column(String(64))
    pool_policy_version: Mapped[str] = mapped_column(String(64), nullable=False)
    ride_plan_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey("ride_plans.id"))
    reason: Mapped[str | None] = mapped_column(String(64))

    __table_args__ = (
        in_check("entry_type", FUND_ENTRY_TYPES, "entry_type"),
        CheckConstraint("(entry_type IN ('CONTRIBUTION', 'CANCEL_FEE_INFLOW', 'INITIAL_SEED') AND amount_signed_vnd > 0)"
                        " OR (entry_type = 'GUARANTEE_PAYOUT' AND amount_signed_vnd < 0)", name="ledger_sign_by_type"),
        CheckConstraint("balance_after_vnd >= 0", name="ledger_balance_non_negative"),
        CheckConstraint("(entry_type = 'INITIAL_SEED') = (booking_id IS NULL)", name="ledger_booking_by_type"),
        CheckConstraint("entry_type = 'INITIAL_SEED' OR pricing_version IS NOT NULL",
                        name="ledger_pricing_version_by_type"),
        Index("uq_fund_ledger_booking_entry", "booking_id", "entry_type", unique=True,
              postgresql_where=text("booking_id IS NOT NULL")),
        Index("uq_fund_ledger_single_seed", "entry_type", unique=True,
              postgresql_where=text("entry_type = 'INITIAL_SEED'")),
    )
