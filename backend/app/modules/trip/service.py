"""trip service - the only code that reads or writes `trip_requests` and
`service_areas`.

Classification uses one service_areas version (settings.service_area_version)
and its two tiers (owner decision GEO-03): the polygon layers, then a per-point
serviceability check against the road network.
Only APPROVED geometry is used unless ALLOW_CANDIDATE_SERVICE_AREA is set for
development; results computed on CANDIDATE geometry are not acceptance
evidence (owner decisions P1-D1 / P1-D3).
"""

import uuid
from collections.abc import Callable
from dataclasses import dataclass, replace
from datetime import UTC, datetime
from typing import Any

from geoalchemy2.elements import WKTElement
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.core.config_baseline import get_config_baseline
from app.core.errors import ApiError
from app.core.settings import Settings
from app.modules.routing.service import OsrmCarDistance, Reachability, RouteNotFound, RoutingUnavailable
from app.modules.trip import rules
from app.modules.trip.models import ServiceArea, TripRequest
from app.modules.trip.schemas import TripRequestIn, TripRequestOut

Lonlat = tuple[float, float]
Exclude = tuple[str, ...]
DistanceFn = Callable[[Lonlat, Lonlat, Exclude], float]
ReachFn = Callable[[Lonlat, Lonlat, Lonlat, Exclude], Reachability]


@dataclass(frozen=True)
class Serviceability:
    """Tier-2 parameters stored with a version (GEO-03): anchor of the 150 km
    road limit, the limit itself, and the maximum snap distance to the car road
    network (implementation parameter, pending owner confirmation)."""

    anchor: Lonlat
    max_road_km: float
    max_snap_m: float
    exclude: Exclude = ()  # OSRM classes never used (GEO-E: ferry)


@dataclass(frozen=True)
class ActiveAreas:
    version: str
    status: str
    serviceability: Serviceability | None


def active_service_areas(session: Session, settings: Settings, require_serviceability: bool = True) -> ActiveAreas:
    version = settings.service_area_version
    if not version:
        raise ApiError(503, "SERVICE_AREA_NOT_CONFIGURED", "No service-area version is configured")
    rows = {t: (st, src) for t, st, src in session.execute(
        select(ServiceArea.area_type, ServiceArea.status, ServiceArea.source_json)
        .where(ServiceArea.service_area_version == version)
    ).tuples().all()}
    if not {"URBAN", "TOTAL"} <= set(rows):
        raise ApiError(503, "SERVICE_AREA_NOT_CONFIGURED", f"Service-area version {version} is incomplete or missing")
    statuses = [st for st, _ in rows.values()]
    if any(s == "RETIRED" for s in statuses):
        raise ApiError(503, "SERVICE_AREA_NOT_CONFIGURED", f"Service-area version {version} is retired")
    if any(s != "APPROVED" for s in statuses) and not settings.allow_candidate_service_area:
        raise ApiError(503, "SERVICE_AREA_NOT_APPROVED",
                       f"Service-area version {version} is not approved by the project owner")
    raw = (rows["TOTAL"][1] or {}).get("serviceability")
    serviceability = None if raw is None else Serviceability(
        anchor=(float(raw["anchor"]["lon"]), float(raw["anchor"]["lat"])),
        max_road_km=float(raw["max_road_km"]), max_snap_m=float(raw["max_snap_m"]),
        exclude=tuple(raw.get("exclude", ())))
    if serviceability is None and require_serviceability:
        raise ApiError(503, "SERVICE_AREA_NOT_CONFIGURED",
                       f"Service-area version {version} has no per-point serviceability layer (GEO-03)")
    status = "APPROVED" if all(s == "APPROVED" for s in statuses) else "CANDIDATE"
    return ActiveAreas(version=version, status=status, serviceability=serviceability)


def point_membership(session: Session, version: str, point: Lonlat) -> dict[str, bool]:
    """Polygon membership per layer; EXCLUDED is False when the version has none."""
    geom = func.ST_SetSRID(func.ST_MakePoint(point[0], point[1]), 4326)
    rows = session.execute(
        select(ServiceArea.area_type, func.ST_Intersects(ServiceArea.geom, geom))
        .where(ServiceArea.service_area_version == version)
    ).tuples().all()
    return {"EXCLUDED": False} | dict(rows)


@dataclass(frozen=True)
class PointAssessment:
    in_urban: bool
    reason: str | None  # None = served; else rules.POLYGON_REASONS / rules.POINT_REASONS
    layer: str | None   # POLYGON (tier 1) | SERVICEABILITY (tier 2)
    anchor_road_km: float | None = None
    snap_m: float | None = None

    def as_json(self) -> dict[str, Any]:
        return {"reason": self.reason, "layer": self.layer,
                "anchor_road_km": None if self.anchor_road_km is None else round(self.anchor_road_km, 3),
                "snap_m": None if self.snap_m is None else round(self.snap_m, 1)}


@dataclass(frozen=True)
class Assessment:
    classification: rules.Classification
    pickup: PointAssessment
    dropoff: PointAssessment
    tier2_applied: bool


def assess(session: Session, areas: ActiveAreas, pickup: Lonlat, dropoff: Lonlat, distance_fn: DistanceFn,
           reach_fn: ReachFn, buffer_km: float) -> Assessment:
    """Section 2.3 classification on a two-tier service area (GEO-03).

    Tier 1 (polygon) needs no routing. Tier 2 runs one OSRM /table request only when
    both points pass tier 1. Raises RouteNotFound when both points are served but no
    route joins them, RoutingUnavailable when OSRM cannot answer (no fallback)."""
    mp, md = point_membership(session, areas.version, pickup), point_membership(session, areas.version, dropoff)
    p_reason = rules.polygon_reason(mp["TOTAL"], mp["EXCLUDED"])
    d_reason = rules.polygon_reason(md["TOTAL"], md["EXCLUDED"])
    p = PointAssessment(mp["URBAN"], p_reason, "POLYGON" if p_reason else None)
    d = PointAssessment(md["URBAN"], d_reason, "POLYGON" if d_reason else None)
    s = areas.serviceability
    tier2 = s is not None and p.reason is None and d.reason is None
    if tier2:
        assert s is not None
        try:
            reach = reach_fn(s.anchor, pickup, dropoff, s.exclude)
        except RouteNotFound:  # OSRM could not snap a point to any road segment
            p = replace(p, reason="NO_ROAD_ACCESS", layer="SERVICEABILITY")
            d = replace(d, reason="NO_ROAD_ACCESS", layer="SERVICEABILITY")
        else:
            def tier2_point(pa: PointAssessment, snap_m: float, anchor_km: float | None) -> PointAssessment:
                reason = rules.point_reason(snap_m, anchor_km, s.max_snap_m, s.max_road_km)
                return replace(pa, reason=reason, layer="SERVICEABILITY" if reason else None,
                               anchor_road_km=anchor_km, snap_m=snap_m)

            p = tier2_point(p, reach.pickup.snap_m, reach.pickup.anchor_road_km)
            d = tier2_point(d, reach.dropoff.snap_m, reach.dropoff.anchor_road_km)
            if p.reason is None and d.reason is None and reach.pickup_to_dropoff_km is None:
                raise RouteNotFound("NoRoute")
    exclude = s.exclude if s is not None else ()
    result = rules.classify(
        pickup_in_total=p.reason is None,
        dropoff_in_total=d.reason is None,
        pickup_in_urban=p.in_urban,
        dropoff_in_urban=d.in_urban,
        road_distance_km=lambda: distance_fn(pickup, dropoff, exclude),
        urban_boundary_buffer_km=buffer_km,
    )
    return Assessment(classification=result, pickup=p, dropoff=d, tier2_applied=tier2)


def osrm_distance_fn(settings: Settings) -> DistanceFn:
    client = OsrmCarDistance(settings.osrm_car_url, settings.routing_timeout_s)
    return lambda a, b, exclude=(): client.road_distance(a, b, exclude).km


def osrm_reach_fn(settings: Settings) -> ReachFn:
    client = OsrmCarDistance(settings.osrm_car_url, settings.routing_timeout_s)
    return client.reachability


def create_trip_request(
    session: Session,
    user_id: uuid.UUID,
    body: TripRequestIn,
    settings: Settings,
    distance_fn: DistanceFn,
    reach_fn: ReachFn,
    now: datetime | None = None,
) -> TripRequestOut:
    now = now or datetime.now(UTC)
    baseline = get_config_baseline()
    areas = active_service_areas(session, settings)

    preferred = now if body.booking_type == "NOW" else body.preferred_departure
    assert preferred is not None
    lead_time = preferred - now
    if lead_time.total_seconds() < 0:
        raise ApiError(422, "DEPARTURE_IN_PAST", "preferred_departure must not be in the past")

    pickup: Lonlat = (body.pickup.lon, body.pickup.lat)
    dropoff: Lonlat = (body.dropoff.lon, body.dropoff.lat)
    try:
        assessed = assess(session, areas, pickup, dropoff, distance_fn, reach_fn,
                          float(baseline["spatial_and_service_areas"]["urban_boundary_buffer_km"]))
    except RouteNotFound as exc:
        raise ApiError(422, "ROUTE_NOT_FOUND", "No road route between pickup and dropoff", {"osrm_code": str(exc)}) from exc
    except RoutingUnavailable as exc:
        raise ApiError(503, "ROUTING_UNAVAILABLE", "Routing service is unavailable") from exc
    result = assessed.classification
    if result.mode is None:
        if result.error_code == "OUT_OF_SERVICE_AREA":
            raise ApiError(422, "OUT_OF_SERVICE_AREA", "Pickup or dropoff is outside the service area",
                           {"service_area_version": areas.version, "pickup": assessed.pickup.as_json(),
                            "dropoff": assessed.dropoff.as_json()})
        raise ApiError(422, str(result.error_code),
                       "Only intercity routes with one end in the Hà Nội urban area are supported",
                       {"service_area_version": areas.version})

    allowed, rejections = rules.allowed_services(
        mode=result.mode,
        vehicle_preference=body.vehicle_preference,
        ride_preference=body.ride_preference,
        passenger_count=body.passenger_count,
        has_luggage=body.has_luggage,
        lead_time=lead_time,
        baseline=baseline,
    )
    trip = TripRequest(
        user_id=user_id,
        mode=result.mode,
        vehicle_preference=body.vehicle_preference,
        ride_preference=body.ride_preference,
        allowed_service_codes=allowed,
        rejection_reasons_json=[r.as_json() for r in rejections],
        booking_type=body.booking_type,
        passenger_count=body.passenger_count,
        has_luggage=body.has_luggage,
        pickup_geom=WKTElement(f"POINT({pickup[0]} {pickup[1]})", srid=4326),
        dropoff_geom=WKTElement(f"POINT({dropoff[0]} {dropoff[1]})", srid=4326),
        preferred_departure=preferred,
        earliest_departure=body.earliest_departure,
        latest_departure=body.latest_departure,
        latest_arrival=body.latest_arrival,
        budget_min=body.budget_min,
        budget_max=body.budget_max,
        max_passenger_detour_ratio=(body.max_passenger_detour_ratio
                                    if body.max_passenger_detour_ratio is not None
                                    else rules.SPEC_DEFAULT_MAX_PASSENGER_DETOUR_RATIO),
        max_in_vehicle_time_s=body.max_in_vehicle_time_s,
        max_walk_m=body.max_walk_m,
        categorical_preferences_json=body.categorical_preferences,
        service_area_version=areas.version,
        direct_distance_km=result.direct_distance_km,
    )
    session.add(trip)
    session.commit()
    return to_out(trip)


def to_out(trip: TripRequest) -> TripRequestOut:
    return TripRequestOut(
        id=trip.id,
        mode=trip.mode,
        booking_type=trip.booking_type,
        preferred_departure=trip.preferred_departure,
        allowed_service_codes=list(trip.allowed_service_codes),
        rejection_reasons=list(trip.rejection_reasons_json),
        direct_distance_km=trip.direct_distance_km,
        max_passenger_detour_ratio=trip.max_passenger_detour_ratio,
        service_area_version=trip.service_area_version,
        created_at=trip.created_at,
    )


def get_trip_request(session: Session, trip_id: uuid.UUID) -> TripRequest | None:
    return session.get(TripRequest, trip_id)


# --- Phase 2: read-only snapshot for candidate generation (Section 6 Trip Intent) ---

@dataclass(frozen=True)
class TripSnapshot:
    request_id: uuid.UUID
    user_id: uuid.UUID
    mode: str
    booking_type: str
    allowed_service_codes: tuple[str, ...]
    passenger_count: int
    has_luggage: bool
    pickup: Lonlat
    dropoff: Lonlat
    preferred_departure: datetime
    earliest_departure: datetime | None
    latest_departure: datetime | None
    latest_arrival: datetime | None
    budget_max: int | None
    max_passenger_detour_ratio: float | None
    max_in_vehicle_time_s: int | None
    max_walk_m: int | None
    same_gender_coride: bool
    created_at: datetime
    service_area_version: str


def trip_snapshots(session: Session, request_ids: list[uuid.UUID]) -> dict[uuid.UUID, TripSnapshot]:
    if not request_ids:
        return {}
    rows = session.execute(select(
        TripRequest, func.ST_X(TripRequest.pickup_geom), func.ST_Y(TripRequest.pickup_geom),
        func.ST_X(TripRequest.dropoff_geom), func.ST_Y(TripRequest.dropoff_geom),
    ).where(TripRequest.id.in_(request_ids))).all()
    out = {}
    for t, plon, plat, dlon, dlat in rows:
        prefs = t.categorical_preferences_json or {}
        out[t.id] = TripSnapshot(
            request_id=t.id, user_id=t.user_id, mode=t.mode, booking_type=t.booking_type,
            allowed_service_codes=tuple(t.allowed_service_codes), passenger_count=t.passenger_count,
            has_luggage=t.has_luggage, pickup=(plon, plat), dropoff=(dlon, dlat),
            preferred_departure=t.preferred_departure, earliest_departure=t.earliest_departure,
            latest_departure=t.latest_departure, latest_arrival=t.latest_arrival, budget_max=t.budget_max,
            max_passenger_detour_ratio=t.max_passenger_detour_ratio, max_in_vehicle_time_s=t.max_in_vehicle_time_s,
            max_walk_m=t.max_walk_m, same_gender_coride=bool(prefs.get("same_gender_coride", False)),
            created_at=t.created_at, service_area_version=t.service_area_version)
    return out
