"""trip service - the only code that reads or writes `trip_requests` and
`service_areas`.

Classification uses one service_areas version (settings.service_area_version).
Only APPROVED geometry is used unless ALLOW_CANDIDATE_SERVICE_AREA is set for
development; results computed on CANDIDATE geometry are not acceptance
evidence (owner decisions P1-D1 / P1-D3).
"""

import uuid
from collections.abc import Callable
from dataclasses import dataclass
from datetime import UTC, datetime

from geoalchemy2.elements import WKTElement
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.core.config_baseline import get_config_baseline
from app.core.errors import ApiError
from app.core.settings import Settings
from app.modules.routing.service import OsrmCarDistance, RouteNotFound, RoutingUnavailable
from app.modules.trip import rules
from app.modules.trip.models import ServiceArea, TripRequest
from app.modules.trip.schemas import TripRequestIn, TripRequestOut

Lonlat = tuple[float, float]
DistanceFn = Callable[[Lonlat, Lonlat], float]


@dataclass(frozen=True)
class ActiveAreas:
    version: str
    status: str


def active_service_areas(session: Session, settings: Settings) -> ActiveAreas:
    version = settings.service_area_version
    if not version:
        raise ApiError(503, "SERVICE_AREA_NOT_CONFIGURED", "No service-area version is configured")
    statuses = dict(session.execute(
        select(ServiceArea.area_type, ServiceArea.status).where(ServiceArea.service_area_version == version)
    ).tuples().all())
    if set(statuses) != {"URBAN", "TOTAL"}:
        raise ApiError(503, "SERVICE_AREA_NOT_CONFIGURED", f"Service-area version {version} is incomplete or missing")
    if any(s == "RETIRED" for s in statuses.values()):
        raise ApiError(503, "SERVICE_AREA_NOT_CONFIGURED", f"Service-area version {version} is retired")
    if any(s != "APPROVED" for s in statuses.values()) and not settings.allow_candidate_service_area:
        raise ApiError(503, "SERVICE_AREA_NOT_APPROVED",
                       f"Service-area version {version} is not approved by the project owner")
    status = "APPROVED" if all(s == "APPROVED" for s in statuses.values()) else "CANDIDATE"
    return ActiveAreas(version=version, status=status)


def point_membership(session: Session, version: str, point: Lonlat) -> dict[str, bool]:
    geom = func.ST_SetSRID(func.ST_MakePoint(point[0], point[1]), 4326)
    rows = session.execute(
        select(ServiceArea.area_type, func.ST_Intersects(ServiceArea.geom, geom))
        .where(ServiceArea.service_area_version == version)
    ).tuples().all()
    return dict(rows)


def osrm_distance_fn(settings: Settings) -> DistanceFn:
    client = OsrmCarDistance(settings.osrm_car_url, settings.routing_timeout_s)
    return lambda a, b: client.road_distance(a, b).km


def create_trip_request(
    session: Session,
    user_id: uuid.UUID,
    body: TripRequestIn,
    settings: Settings,
    distance_fn: DistanceFn,
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
    p_in = point_membership(session, areas.version, pickup)
    d_in = point_membership(session, areas.version, dropoff)
    try:
        result = rules.classify(
            pickup_in_total=p_in["TOTAL"],
            dropoff_in_total=d_in["TOTAL"],
            pickup_in_urban=p_in["URBAN"],
            dropoff_in_urban=d_in["URBAN"],
            road_distance_km=lambda: distance_fn(pickup, dropoff),
            urban_boundary_buffer_km=float(baseline["spatial_and_service_areas"]["urban_boundary_buffer_km"]),
        )
    except RouteNotFound as exc:
        raise ApiError(422, "ROUTE_NOT_FOUND", "No road route between pickup and dropoff", {"osrm_code": str(exc)}) from exc
    except RoutingUnavailable as exc:
        raise ApiError(503, "ROUTING_UNAVAILABLE", "Routing service is unavailable") from exc
    if result.mode is None:
        message = ("Pickup or dropoff is outside the service area" if result.error_code == "OUT_OF_SERVICE_AREA"
                   else "Only intercity routes with one end in the Hà Nội urban area are supported")
        raise ApiError(422, str(result.error_code), message, {"service_area_version": areas.version})

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
