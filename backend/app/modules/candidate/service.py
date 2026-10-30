"""candidate service - runs a generation and stores it: one `candidate_runs` row (policy,
stage timings, counts, rejections per hard constraint) and one `ride_candidates` row per
feasible candidate. These rows are the event log of the later ranking and P(match) /
P(fulfill) work (P6-P8); nothing here ranks or offers.

Routing failures are explicit (no straight-line fallback): the run is stored with its
status and the API answers 503 ROUTING_UNAVAILABLE / MATRIX_TOO_LARGE or 422
ROUTE_NOT_FOUND."""

import uuid
from datetime import UTC, datetime
from typing import Any

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.errors import ApiError
from app.core.settings import Settings
from app.modules.candidate.generator import RunResult, generate
from app.modules.candidate.models import CandidateRun, RideCandidate
from app.modules.routing.factory import osrm_provider, policy_for
from app.modules.routing.provider import MatrixTooLarge, RouteNotFound, RoutingProvider, RoutingUnavailable
from app.modules.trip.service import active_service_areas, trip_snapshots

ERRORS = {RoutingUnavailable: ("ROUTING_UNAVAILABLE", 503), MatrixTooLarge: ("MATRIX_TOO_LARGE", 503),
          RouteNotFound: ("ROUTE_NOT_FOUND", 422)}


def run(session: Session, settings: Settings, request_id: uuid.UUID, provider: RoutingProvider | None = None,
        now: datetime | None = None) -> tuple[CandidateRun, RunResult]:
    trip = trip_snapshots(session, [request_id]).get(request_id)
    if trip is None:
        raise ApiError(404, "NOT_FOUND", "Trip request not found")
    areas = active_service_areas(session, settings)
    policy = policy_for(settings, areas.serviceability.exclude if areas.serviceability else ())
    provider = provider or osrm_provider(settings, policy)
    now = now or datetime.now(UTC)
    try:
        result = generate(session, settings, trip, provider, now)
    except (RoutingUnavailable, MatrixTooLarge, RouteNotFound) as exc:
        status = next(code for cls, (code, _) in ERRORS.items() if isinstance(exc, cls))
        result = RunResult(status=status, error=str(exc))
    stored = CandidateRun(request_id=request_id, status=result.status,
                          routing_policy_json={"exclude": list(policy.exclude), "routing_version": policy.routing_version,
                                               "service_area_version": areas.version},
                          osrm_requests=result.osrm_requests, timings_json=result.timings_ms,
                          counts_json=result.counts | ({"error": result.error} if result.error else {}),
                          rejections_json=result.rejections)
    session.add(stored)
    session.flush()
    for c in result.candidates:
        session.add(RideCandidate(
            request_id=request_id, run_id=stored.id, service_code=c.service_code, candidate_source_type=c.source_type,
            target_plan_id=c.plan_id, source_plan_version=c.plan_version, seat_count=c.seat_count, walk_m=0,
            private_fare_ref_vnd=c.private_fare_vnd, pool_quote_price_vnd=c.pool_quote_vnd,
            pool_unmatched_price_vnd=c.pool_unmatched_vnd, expected_price_vnd=c.expected_price_vnd,
            driver_id=c.driver_id, vehicle_id=c.vehicle_id, pickup_eta_s=round(c.pickup_eta_s),
            direct_distance_m=c.direct_distance_m, direct_duration_s=c.direct_duration_s,
            pricing_check=c.pricing_check, insertion_json=c.insertion, constraint_audit_json=c.audit))
    session.commit()
    if result.status != "OK":
        code, http = next(v for cls, v in ERRORS.items() if v[0] == result.status)
        raise ApiError(http, code, result.error or code, {"run_id": str(stored.id)})
    return stored, result


def run_out(session: Session, run_id: uuid.UUID) -> dict[str, Any]:
    stored = session.get(CandidateRun, run_id)
    if stored is None:
        raise ApiError(404, "NOT_FOUND", "Candidate run not found")
    rows = session.scalars(select(RideCandidate).where(RideCandidate.run_id == run_id)
                           .order_by(RideCandidate.service_code, RideCandidate.pickup_eta_s)).all()
    return {"run_id": stored.id, "request_id": stored.request_id, "created_at": stored.created_at,
            "status": stored.status, "routing_policy": stored.routing_policy_json, "osrm_requests": stored.osrm_requests,
            "timings_ms": stored.timings_json, "counts": stored.counts_json, "rejections": stored.rejections_json,
            "candidates": [{"id": r.id, "service_code": r.service_code, "source_type": r.candidate_source_type,
                            "driver_id": r.driver_id, "vehicle_id": r.vehicle_id, "target_plan_id": r.target_plan_id,
                            "source_plan_version": r.source_plan_version, "pickup_eta_s": r.pickup_eta_s,
                            "direct_distance_m": r.direct_distance_m, "direct_duration_s": r.direct_duration_s,
                            "private_fare_ref_vnd": r.private_fare_ref_vnd, "expected_price_vnd": r.expected_price_vnd,
                            "pool_quote_price_vnd": r.pool_quote_price_vnd,
                            "pool_unmatched_price_vnd": r.pool_unmatched_price_vnd, "pricing_check": r.pricing_check,
                            "insertion": r.insertion_json, "constraint_audit": r.constraint_audit_json}
                           for r in rows]}

