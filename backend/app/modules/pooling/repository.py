"""Read open pool plans for Section 35.2 branch A: plan header, stop chain (ride_stops)
and participants. Writes to plans happen in the ride lifecycle (Phase 4)."""

import uuid
from dataclasses import dataclass
from datetime import datetime

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.modules.pooling.models import RideParticipant, RidePlan, RideStop


@dataclass(frozen=True)
class StopRecord:
    seq: int
    kind: str
    booking_id: uuid.UUID
    lon: float
    lat: float
    status: str
    completed_at: datetime | None


@dataclass(frozen=True)
class PlanRecord:
    plan_id: uuid.UUID
    plan_version: int
    driver_id: uuid.UUID
    completed_stop_index: int
    stops: tuple[StopRecord, ...]                   # seq order
    traveled_m: dict[uuid.UUID, float]              # booking -> distance ridden since boarding
    direct: dict[uuid.UUID, tuple[float, float]]    # booking -> direct trip (m, s) fixed at booking


def open_plan_drivers(session: Session) -> dict[uuid.UUID, uuid.UUID]:
    """driver_id -> plan_id of every plan still accepting riders (PLAN_OPEN_SEARCHING)."""
    rows = session.execute(select(RidePlan.driver_id, RidePlan.id)
                           .where(RidePlan.status == "PLAN_OPEN_SEARCHING")).tuples().all()
    return dict(rows)


def plan_records(session: Session, plan_ids: list[uuid.UUID]) -> list[PlanRecord]:
    if not plan_ids:
        return []
    heads = session.execute(select(RidePlan.id, RidePlan.plan_version, RidePlan.driver_id,
                                   RidePlan.completed_stop_index).where(RidePlan.id.in_(plan_ids))).all()
    stops: dict[uuid.UUID, list[StopRecord]] = {pid: [] for pid in plan_ids}
    for s, lon, lat in session.execute(
            select(RideStop, func.ST_X(RideStop.geom), func.ST_Y(RideStop.geom))
            .where(RideStop.ride_plan_id.in_(plan_ids)).order_by(RideStop.ride_plan_id, RideStop.seq)).all():
        stops[s.ride_plan_id].append(StopRecord(s.seq, s.kind, s.booking_id, lon, lat, s.status, s.completed_at))
    traveled: dict[uuid.UUID, dict[uuid.UUID, float]] = {pid: {} for pid in plan_ids}
    direct: dict[uuid.UUID, dict[uuid.UUID, tuple[float, float]]] = {pid: {} for pid in plan_ids}
    for plan_id, booking_id, km, d_m, d_s in session.execute(
            select(RideParticipant.ride_plan_id, RideParticipant.booking_id,
                   RideParticipant.traveled_km_before_last_replan, RideParticipant.direct_distance_m,
                   RideParticipant.direct_duration_s)
            .where(RideParticipant.ride_plan_id.in_(plan_ids))).tuples().all():
        traveled[plan_id][booking_id] = km * 1000.0
        if d_m is not None and d_s is not None:
            direct[plan_id][booking_id] = (d_m, d_s)
    return [PlanRecord(pid, version, driver, r, tuple(stops[pid]), traveled[pid], direct[pid])
            for pid, version, driver, r in heads]
