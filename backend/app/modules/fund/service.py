"""fund service - the guarantee-fund ledger and driver payouts (Revision 9 Sections 17.2, 18.3-18.5,
18.7, 19.1; gates G12 / G18).

Rules enforced here and, as a backstop, by the database (migration 0006):
- `fund_ledger` is append-only; each entry continues the balance chain (balance_after = previous
  balance + amount) under one advisory lock, so concurrent writers cannot fork it;
- the sign of an entry follows its type, and the balance can never go negative (as on the
  Phase 9 contract, where `guaranteeFundBalance` is a uint256): a guarantee the fund cannot pay
  raises `FundInsufficient` - it is never booked against a negative balance;
- one entry per (booking, type), one INITIAL_SEED; every non-seed entry names its booking and the
  pricing_version / pool_policy_version that produced it;
- one `driver_payouts` row per booking (immutable), whose split adds up to the amount charged;
  settling the same booking twice with the same numbers is a no-op, with different numbers an error.

Nothing here talks to a blockchain: `onchain_tx_hash` stays NULL until Phase 9 fills it through
`fund.chain.FundChainSync` (no on-chain transaction is simulated).
"""

import uuid
from collections.abc import Mapping
from dataclasses import dataclass, field
from fractions import Fraction
from typing import Any

from sqlalchemy import func, select, text
from sqlalchemy.orm import Session

from app.modules.booking import service as booking_service
from app.modules.booking.service import BookingView
from app.modules.fund.models import DriverPayout, FundLedgerEntry
from app.modules.pooling import pricing_state
from app.modules.pricing.cancellation import CancelOutcome
from app.modules.pricing.params import PricingParams
from app.modules.pricing.settlement import (
    Settlement,
    settle_fixed,
    settle_intercity_pool,
    settle_pool_matched,
    settle_pool_unmatched,
)

CHAIN_LOCK = "SELECT pg_advisory_xact_lock(hashtext('fund_ledger_chain'))"
LOCKED_PRICE_STATUSES = ("FIXED_LOCKED", "MATCHED_LOCKED", "UNMATCHED_LOCKED", "TOPUP_LOCKED", "MERGED_REDUCED_LOCKED")


class FundError(RuntimeError):
    pass


class FundInsufficient(FundError):
    """The guarantee fund cannot pay this amount without going negative."""


class SettlementConflict(FundError):
    """The booking was already settled with different amounts."""


def balance(session: Session) -> int:
    last = session.scalar(select(FundLedgerEntry.balance_after_vnd).order_by(FundLedgerEntry.id.desc()).limit(1))
    return int(last or 0)


def append_entry(session: Session, entry_type: str, amount: int, *, booking_id: uuid.UUID | None,
                 pricing_version: str | None, pool_policy_version: str, ride_plan_id: uuid.UUID | None = None,
                 reason: str | None = None) -> FundLedgerEntry:
    """One ledger entry, in the caller's transaction (no commit)."""
    session.execute(text(CHAIN_LOCK))
    after = balance(session) + amount
    if after < 0:
        raise FundInsufficient(f"fund balance {after - amount} cannot pay {-amount}")
    entry = FundLedgerEntry(entry_type=entry_type, booking_id=booking_id, amount_signed_vnd=amount,
                            balance_after_vnd=after, pricing_version=pricing_version,
                            pool_policy_version=pool_policy_version, ride_plan_id=ride_plan_id, reason=reason)
    session.add(entry)
    session.flush()
    return entry


def seed_fund(session: Session, baseline: Mapping[str, Any]) -> FundLedgerEntry:
    """INITIAL_SEED from `booking_and_concurrency.initial_guarantee_fund_seed_vnd`, once."""
    amount = int(baseline["booking_and_concurrency"]["initial_guarantee_fund_seed_vnd"])
    existing = session.scalar(select(FundLedgerEntry).where(FundLedgerEntry.entry_type == "INITIAL_SEED"))
    if existing is not None:
        if existing.amount_signed_vnd != amount:
            raise FundError(f"fund already seeded with {existing.amount_signed_vnd}, baseline says {amount}")
        return existing
    entry = append_entry(session, "INITIAL_SEED", amount, booking_id=None, pricing_version=None,
                         pool_policy_version=baseline["pool_policy_version"], reason="initial_guarantee_fund_seed_vnd")
    session.commit()
    return entry


def _same(row: DriverPayout, s: Settlement, driver_id: uuid.UUID, version: str) -> bool:
    return (row.driver_id, row.payout_kind, row.gross_fare_charged_vnd, row.driver_base_amount_vnd,
            row.platform_net_amount_vnd, row.fund_contribution_vnd, row.guarantee_amount_vnd,
            row.total_driver_payout_vnd, row.unmatched_cause, row.pricing_version) == (
        driver_id, s.kind, s.gross_charged, s.driver_base, s.platform_net, s.fund_contribution, s.guarantee,
        s.total_driver, s.unmatched_cause, version)


def record_settlement(session: Session, *, booking_id: uuid.UUID, driver_id: uuid.UUID, settlement: Settlement,
                      pricing_version: str, pool_policy_version: str, ride_plan_id: uuid.UUID | None = None,
                      commit: bool = True) -> DriverPayout:
    """Payout row + fund entries of one booking, atomically. Idempotent on identical numbers."""
    settlement.check()
    existing = session.scalar(select(DriverPayout).where(DriverPayout.booking_id == booking_id))
    if existing is not None:
        if _same(existing, settlement, driver_id, pricing_version):
            return existing
        raise SettlementConflict(f"booking {booking_id} already settled with different amounts")
    try:
        row = DriverPayout(booking_id=booking_id, driver_id=driver_id, payout_kind=settlement.kind,
                           gross_fare_charged_vnd=settlement.gross_charged, driver_base_amount_vnd=settlement.driver_base,
                           guarantee_amount_vnd=settlement.guarantee, total_driver_payout_vnd=settlement.total_driver,
                           commission_rate=float(settlement.commission_rate),
                           platform_net_amount_vnd=settlement.platform_net,
                           fund_contribution_vnd=settlement.fund_contribution, pricing_version=pricing_version,
                           pool_policy_version=pool_policy_version, unmatched_cause=settlement.unmatched_cause)
        session.add(row)
        session.flush()
        common = dict(booking_id=booking_id, pricing_version=pricing_version, pool_policy_version=pool_policy_version,
                      ride_plan_id=ride_plan_id)
        if settlement.fund_contribution:
            kind = "CANCEL_FEE_INFLOW" if settlement.kind == "CANCELLATION_FEE" else "CONTRIBUTION"
            append_entry(session, kind, settlement.fund_contribution, reason=settlement.kind, **common)  # type: ignore[arg-type]
        if settlement.guarantee:
            append_entry(session, "GUARANTEE_PAYOUT", -settlement.guarantee,
                         reason=settlement.unmatched_cause, **common)  # type: ignore[arg-type]
        if commit:
            session.commit()
        return row
    except Exception:
        session.rollback()
        raise


def cancellation_settlement(outcome: CancelOutcome) -> Settlement:
    """The fee of a cancellation / no-show as a payout of the booking's driver (Section 18.7)."""
    if outcome.fee <= 0:
        raise FundError("a free cancellation pays nobody")
    s = Settlement("CANCELLATION_FEE", outcome.fee, Fraction(outcome.to_platform + outcome.to_fund, outcome.fee),
                   outcome.to_driver, outcome.to_platform, outcome.to_fund, 0)
    s.check()
    return s


@dataclass(frozen=True)
class BookingSettlement:
    booking: BookingView
    settlement: Settlement
    ride_plan_id: uuid.UUID | None


def settlement_for_completed_booking(session: Session, params: PricingParams, booking_id: uuid.UUID,
                                     intercity_confirmation: str | None = None,
                                     corider_cancel_to_driver: int = 0) -> BookingSettlement:
    """Derive the settlement of a COMPLETED booking from its locked price (Phase 4 / 5 call this at
    completion; P3 provides it). The booking's own pricing_version must be the one of `params`."""
    b = booking_service.booking_views(session, [booking_id]).get(booking_id)
    if b is None:
        raise FundError(f"booking {booking_id} not found")
    if b.ride_status != "COMPLETED" or b.price_status not in LOCKED_PRICE_STATUSES or b.final_price_vnd is None:
        raise FundError(f"booking {booking_id} is not completed with a locked final price")
    if b.pricing_version != params.pricing_version:
        raise FundError(f"booking priced with {b.pricing_version}, settlement asked with {params.pricing_version}")
    if b.service_code in ("BIKE_URBAN", "CAR_URBAN_PRIVATE", "CAR_INTERCITY_PRIVATE"):
        return BookingSettlement(b, settle_fixed(params, b.service_code, b.final_price_vnd), None)
    if b.service_code == "CAR_INTERCITY_POOL":
        if intercity_confirmation is None:
            raise FundError("intercity pool settlement needs the T-72h confirmation outcome")
        return BookingSettlement(b, settle_intercity_pool(params, b.final_price_vnd, intercity_confirmation), None)
    part = pricing_state.participant_private_fare(session, booking_id)
    if part is None or part[0] is None:
        raise FundError(f"pool booking {booking_id} has no participant row with P_i")
    private, plan_id = part
    if b.price_status == "MATCHED_LOCKED":
        s = settle_pool_matched(params, b.final_price_vnd, b.unmatched_cause, private=private,
                                corider_cancel_to_driver=corider_cancel_to_driver)
    else:
        s = settle_pool_unmatched(params, private, b.final_price_vnd, b.unmatched_cause)
    return BookingSettlement(b, s, plan_id)


@dataclass
class ReconcileReport:
    entries: int = 0
    balance: int = 0
    sum_of_amounts: int = 0
    chain_breaks: list[int] = field(default_factory=list)
    payout_mismatches: list[str] = field(default_factory=list)
    orphan_entries: list[int] = field(default_factory=list)

    @property
    def ok(self) -> bool:
        return (not self.chain_breaks and not self.payout_mismatches and not self.orphan_entries
                and self.balance == self.sum_of_amounts)


def reconcile(session: Session) -> ReconcileReport:
    """Gate G12: 0 VND difference between the ledger balance and the money of the trips."""
    rep = ReconcileReport()
    running = 0
    by_booking: dict[tuple[uuid.UUID, str], int] = {}
    for e in session.scalars(select(FundLedgerEntry).order_by(FundLedgerEntry.id)):
        rep.entries += 1
        running += e.amount_signed_vnd
        if e.balance_after_vnd != running:
            rep.chain_breaks.append(e.id)
        if e.booking_id is not None:
            by_booking[(e.booking_id, e.entry_type)] = e.amount_signed_vnd
    rep.sum_of_amounts = running
    rep.balance = balance(session)
    payouts = {p.booking_id: p for p in session.scalars(select(DriverPayout))}
    for p in payouts.values():
        inflow = by_booking.get((p.booking_id, "CANCEL_FEE_INFLOW" if p.payout_kind == "CANCELLATION_FEE"
                                 else "CONTRIBUTION"), 0)
        outflow = -by_booking.get((p.booking_id, "GUARANTEE_PAYOUT"), 0)
        if inflow != p.fund_contribution_vnd or outflow != p.guarantee_amount_vnd:
            rep.payout_mismatches.append(str(p.booking_id))
    for (booking_id, _), _amount in by_booking.items():
        if booking_id not in payouts:
            rep.orphan_entries.extend(e for e in session.scalars(
                select(FundLedgerEntry.id).where(FundLedgerEntry.booking_id == booking_id)))
    rep.orphan_entries = sorted(set(rep.orphan_entries))
    return rep


def ledger_total(session: Session) -> int:
    return int(session.scalar(select(func.coalesce(func.sum(FundLedgerEntry.amount_signed_vnd), 0))))
