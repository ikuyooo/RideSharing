"""booking service - Phase 2 read access only (the booking lifecycle is Phase 4)."""

import uuid
from dataclasses import dataclass

from sqlalchemy import select
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


def booking_views(session: Session, booking_ids: list[uuid.UUID]) -> dict[uuid.UUID, BookingView]:
    if not booking_ids:
        return {}
    rows = session.scalars(select(Booking).where(Booking.id.in_(booking_ids))).all()
    return {b.id: BookingView(booking_id=b.id, request_id=b.request_id, user_id=b.user_id, service_code=b.service_code,
                              seat_count=b.seat_count, ride_status=b.ride_status, price_status=b.price_status,
                              quoted_price_cap_vnd=b.quoted_price_cap_vnd) for b in rows}
