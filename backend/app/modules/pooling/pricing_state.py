"""Pricing state of pool plans (pooling owns ride_plans / ride_participants / ride_stops): read the
state of open plans (input of the D1-D6 check, `pricing.pool_check`) and store an accepted allocation
for one plan version. Pure computation lives in `pricing.pool`; bookings are read and written
through `booking.service`.

Storing is guarded twice against overwriting newer or frozen results:
- the plan row is updated only `WHERE plan_version = :expected` (a result computed on an older
  version of the plan is refused with `StalePlanVersion`, Section 42 / gate G04);
- frozen riders (group L) are never written; the database trigger of migration 0006 rejects any
  change to a frozen participant's fares and to a locked pool booking's final price (G08)."""

import math
import uuid
from dataclasses import dataclass
from datetime import datetime
from fractions import Fraction

from sqlalchemy import select, update
from sqlalchemy.orm import Session

from app.modules.booking import service as booking_service
from app.modules.pooling.models import RideParticipant, RidePlan, RideStop
from app.modules.pricing.money import exact_vnd, from_rational_text, to_numeric_2, to_rational_text
from app.modules.pricing.pool import PoolPricing


class StalePlanVersion(RuntimeError):
    pass


@dataclass(frozen=True)
class ParticipantPricing:
    booking_id: uuid.UUID
    seats: int
    private_fare: int | None
    direct_distance_m: float | None
    direct_duration_s: float | None
    price_status: str
    dropped_off: bool
    is_price_frozen: bool
    fare_exact: Fraction | None
    fare_charged: int | None
    final_price: int | None


@dataclass(frozen=True)
class PlanPricingState:
    plan_id: uuid.UUID
    plan_version: int
    status: str
    pricing_version: str | None
    plan_fare_exact: Fraction | None
    driven_m_since_start: float
    started_at: datetime | None
    participants: tuple[ParticipantPricing, ...]


def plan_pricing_states(session: Session, plan_ids: list[uuid.UUID]) -> dict[uuid.UUID, PlanPricingState]:
    if not plan_ids:
        return {}
    dropped = {b for (b,) in session.execute(select(RideStop.booking_id).where(
        RideStop.ride_plan_id.in_(plan_ids), RideStop.kind == "DROPOFF", RideStop.status == "COMPLETED")).all()}
    parts: dict[uuid.UUID, list[ParticipantPricing]] = {pid: [] for pid in plan_ids}
    rows = session.scalars(select(RideParticipant).where(RideParticipant.ride_plan_id.in_(plan_ids))).all()
    views = booking_service.booking_views(session, [r.booking_id for r in rows])
    for part in rows:
        view = views.get(part.booking_id)
        exact = from_rational_text(part.fare_exact_rational) if part.fare_exact_rational else None
        parts[part.ride_plan_id].append(ParticipantPricing(
            booking_id=part.booking_id, seats=part.seat_count or (view.seat_count if view else 1),
            private_fare=part.private_fare_vnd, direct_distance_m=part.direct_distance_m,
            direct_duration_s=part.direct_duration_s, price_status=view.price_status if view else "MISSING",
            dropped_off=part.booking_id in dropped, is_price_frozen=part.is_price_frozen,
            fare_exact=exact, fare_charged=part.fare_charged_vnd, final_price=view.final_price_vnd if view else None))
    out = {}
    for plan in session.scalars(select(RidePlan).where(RidePlan.id.in_(plan_ids))):
        out[plan.id] = PlanPricingState(
            plan_id=plan.id, plan_version=plan.plan_version, status=plan.status, pricing_version=plan.pricing_version,
            plan_fare_exact=from_rational_text(plan.plan_fare_exact) if plan.plan_fare_exact else None,
            driven_m_since_start=plan.driven_m_since_start, started_at=plan.started_at,
            participants=tuple(sorted(parts[plan.id], key=lambda x: str(x.booking_id))))
    return out


def store_plan_pricing(session: Session, plan_id: uuid.UUID, expected_version: int, pricing: PoolPricing,
                       booking_of: dict[str, uuid.UUID], detours: dict[str, float] | None = None) -> int:
    """Write an accepted allocation for `expected_version` of the plan and bump the version.
    `booking_of` maps the rider references of `pricing` to bookings that already have a
    participant row (the new rider's booking is created by Phase 4 before this call).
    Returns the new plan_version."""
    if not pricing.ok or pricing.plan_fare is None:
        raise ValueError("only an accepted pricing can be stored")
    floor_vnd = int(pricing.plan_fare)  # plan_fare_vnd is BIGINT: whole-VND part; the exact value is plan_fare_exact
    res = session.execute(update(RidePlan).where(RidePlan.id == plan_id, RidePlan.plan_version == expected_version)
                          .values(plan_fare_exact=to_rational_text(pricing.plan_fare), plan_fare_vnd=floor_vnd,
                                  plan_version=expected_version + 1))
    if res.rowcount != 1:
        session.rollback()
        raise StalePlanVersion(f"plan {plan_id} is no longer at version {expected_version}")
    for ref, price in pricing.prices.items():
        if price.group == "L":
            continue  # frozen: never written
        booking_id = booking_of[ref]
        values = dict(private_fare_vnd=price.private_fare,
                      # BIGINT bounds, conservative in whole VND (the exact ones follow from P_i and the
                      # previous fare_exact_rational): floor rounded down, dynamic cap rounded up
                      floor_fare_vnd=math.floor(price.floor),  # type: ignore[arg-type]
                      cap_fare_vnd=exact_vnd(price.quote_cap),
                      dynamic_cap_fare_vnd=None if price.effective_cap == price.quote_cap
                      else math.ceil(price.effective_cap),  # type: ignore[arg-type]
                      fare_exact_vnd=to_numeric_2(price.fare_exact),
                      fare_exact_rational=to_rational_text(price.fare_exact),
                      fare_charged_vnd=price.fare_charged, rounding_absorbed_vnd=to_numeric_2(price.rounding_absorbed),
                      allocation_weight=float(price.weight))  # type: ignore[arg-type]
        if detours and ref in detours:
            values["detour_ratio"] = detours[ref]
        n = session.execute(update(RideParticipant).where(RideParticipant.booking_id == booking_id,
                                                          RideParticipant.ride_plan_id == plan_id,
                                                          RideParticipant.is_price_frozen.is_(False))
                            .values(**values)).rowcount
        if n != 1:
            session.rollback()
            raise StalePlanVersion(f"participant {booking_id} of plan {plan_id} is missing or frozen")
        booking_service.set_current_estimated_price(session, booking_id, price.fare_charged)
    session.commit()
    return expected_version + 1


def participant_private_fare(session: Session, booking_id: uuid.UUID) -> tuple[int | None, uuid.UUID] | None:
    """(P_i, ride_plan_id) of a pool booking's participant row, or None."""
    row = session.execute(select(RideParticipant.private_fare_vnd, RideParticipant.ride_plan_id)
                          .where(RideParticipant.booking_id == booking_id)).first()
    return (row[0], row[1]) if row else None
