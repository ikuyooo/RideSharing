"""candidate module tables (Revision 9, Section 54). `ride_candidates`: Section 56.1
item 5. Phase 2 TECHNICAL ADDITIONS: `candidate_runs` (one row per generation run:
routing policy, stage timings, counts, rejections per hard constraint - the event log
the ranking / P(match) models of P6-P8 learn from) and the audit columns of
`ride_candidates` (driver, vehicle, ETA, insertion, constraint audit)."""

import uuid
from datetime import datetime
from typing import Any

from sqlalchemy import BigInteger, DateTime, Float, ForeignKey, Integer, String, func, text
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base
from app.db.types import SERVICE_CODES, in_check

CANDIDATE_SOURCE_TYPES = ("NEW_SINGLE_VEHICLE", "EXISTING_POOL_PLAN", "SCHEDULED_INTERCITY_TRIP")
RUN_STATUSES = ("OK", "ROUTING_UNAVAILABLE", "ROUTE_NOT_FOUND", "MATRIX_TOO_LARGE")
PRICING_CHECKS = ("COMPLETE", "PENDING_P3")


class CandidateRun(Base):
    __tablename__ = "candidate_runs"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, server_default=text("gen_random_uuid()")
    )
    request_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("trip_requests.id"), nullable=False, index=True
    )
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, server_default=func.now())
    status: Mapped[str] = mapped_column(String(24), nullable=False)
    routing_policy_json: Mapped[Any] = mapped_column(JSONB, nullable=False)
    osrm_requests: Mapped[int] = mapped_column(Integer, nullable=False)
    timings_json: Mapped[Any] = mapped_column(JSONB, nullable=False)
    counts_json: Mapped[Any] = mapped_column(JSONB, nullable=False)
    rejections_json: Mapped[Any] = mapped_column(JSONB, nullable=False)

    __table_args__ = (in_check("status", RUN_STATUSES, "status"),)


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

    # --- TECHNICAL ADDITIONS (Phase 2) ---------------------------------------
    run_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("candidate_runs.id", ondelete="CASCADE"), index=True
    )
    driver_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey("driver_profiles.user_id"))
    vehicle_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey("vehicles.id"))
    pickup_eta_s: Mapped[int | None] = mapped_column(Integer)
    direct_distance_m: Mapped[float | None] = mapped_column(Float)
    direct_duration_s: Mapped[float | None] = mapped_column(Float)
    pricing_check: Mapped[str | None] = mapped_column(String(16))
    insertion_json: Mapped[Any | None] = mapped_column(JSONB)
    constraint_audit_json: Mapped[Any | None] = mapped_column(JSONB)

    __table_args__ = (
        in_check("service_code", SERVICE_CODES, "service_code"),
        in_check("candidate_source_type", CANDIDATE_SOURCE_TYPES, "candidate_source_type"),
        in_check("pricing_check", PRICING_CHECKS, "pricing_check"),
    )
