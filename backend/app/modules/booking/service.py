"""booking service - read access (Phase 2) and the price field Phase 3 maintains (the booking
lifecycle itself is Phase 4)."""

import uuid
from dataclasses import dataclass

from sqlalchemy import select, update
from sqlalchemy.orm import Session

from app.modules.booking.models import Booking


@dataclass(frozen=True)
class BookingView:
    booking_id: uuid.UUID
    request_id: uuid.UUID
    user_id: uuid.UUID
    service_code: str
    seat_count: int
    ride_status: str
    price_status: str
    quoted_price_cap_vnd: int | None
    final_price_vnd: int | None = None
    unmatched_cause: str = "NONE"
    pricing_version: str | None = None
    driver_id: uuid.UUID | None = None


def booking_views(session: Session, booking_ids: list[uuid.UUID]) -> dict[uuid.UUID, BookingView]:
    if not booking_ids:
        return {}
    rows = session.scalars(select(Booking).where(Booking.id.in_(booking_ids))).all()
    return {b.id: BookingView(booking_id=b.id, request_id=b.request_id, user_id=b.user_id, service_code=b.service_code,
                              seat_count=b.seat_count, ride_status=b.ride_status, price_status=b.price_status,
                              quoted_price_cap_vnd=b.quoted_price_cap_vnd, final_price_vnd=b.final_price_vnd,
                              unmatched_cause=b.unmatched_cause, pricing_version=b.pricing_version,
                              driver_id=b.driver_id) for b in rows}


def set_current_estimated_price(session: Session, booking_id: uuid.UUID, price_vnd: int) -> None:
    """Section 20.3: current_estimated_price follows the allocation (capped by Quote_i, hence by
    quoted_price_cap). No commit - part of the caller's transaction."""
    session.execute(update(Booking).where(Booking.id == booking_id).values(current_estimated_price_vnd=price_vnd))
