"""candidate module tables (Revision 9, Section 54). Schema only in Phase 1;
candidate generation is Phase 2. `ride_candidates`: Section 56.1 item 5."""

import uuid
from typing import Any

from sqlalchemy import BigInteger, Float, ForeignKey, Integer, String, text
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base
from app.db.types import SERVICE_CODES, in_check

CANDIDATE_SOURCE_TYPES = ("NEW_SINGLE_VEHICLE", "EXISTING_POOL_PLAN", "SCHEDULED_INTERCITY_TRIP")


class RideCandidate(Base):
    __tablename__ = "ride_candidates"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, server_default=text("gen_random_uuid()")
    )
    request_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("trip_requests.id"), nullable=False, index=True
    )
    service_code: Mapped[str] = mapped_column(String(32), nullable=False)
    candidate_source_type: Mapped[str] = mapped_column(String(32), nullable=False)
    target_plan_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey("ride_plans.id"))
    scheduled_trip_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("scheduled_trips.id")
    )
    source_plan_version: Mapped[int | None] = mapped_column(Integer)
    seat_count: Mapped[int | None] = mapped_column(Integer)
    pickup_point_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("pickup_points.id")
    )
    walk_m: Mapped[int] = mapped_column(Integer, nullable=False, server_default="0")
    private_fare_ref_vnd: Mapped[int | None] = mapped_column(BigInteger)
    effective_private_fare_vnd: Mapped[int | None] = mapped_column(BigInteger)
    pool_quote_price_vnd: Mapped[int | None] = mapped_column(BigInteger)
    pool_unmatched_price_vnd: Mapped[int | None] = mapped_column(BigInteger)
    fare_matched_est_vnd: Mapped[int | None] = mapped_column(BigInteger)
    expected_price_vnd: Mapped[int | None] = mapped_column(BigInteger)
    door_surcharge_vnd: Mapped[int] = mapped_column(BigInteger, nullable=False, server_default="0")
    shareability_ratio: Mapped[float | None] = mapped_column(Float)
    p_match_est: Mapped[float | None] = mapped_column(Float)
    p_fulfill_est: Mapped[float | None] = mapped_column(Float)
    p_fill_est: Mapped[float | None] = mapped_column(Float)
    model_versions_json: Mapped[Any | None] = mapped_column(JSONB)

    __table_args__ = (
        in_check("service_code", SERVICE_CODES, "service_code"),
        in_check("candidate_source_type", CANDIDATE_SOURCE_TYPES, "candidate_source_type"),
    )
