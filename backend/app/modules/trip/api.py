import uuid

from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from app.core.errors import ApiError
from app.core.settings import Settings, get_settings
from app.db.session import get_db
from app.modules.identity.deps import User, ensure_owner_or_admin, get_current_user, require_roles
from app.modules.trip import service
from app.modules.trip.schemas import TripRequestIn, TripRequestOut

router = APIRouter(tags=["trip"])


def get_distance_fn(settings: Settings = Depends(get_settings)) -> service.DistanceFn:
    """Overridable in tests; production uses the OSRM car profile (P1-D2)."""
    return service.osrm_distance_fn(settings)


@router.post("/api/trip-requests", response_model=TripRequestOut, status_code=status.HTTP_201_CREATED)
def create_trip_request(
    body: TripRequestIn,
    user: User = Depends(require_roles("PASSENGER")),
    session: Session = Depends(get_db),
    settings: Settings = Depends(get_settings),
    distance_fn: service.DistanceFn = Depends(get_distance_fn),
) -> TripRequestOut:
    return service.create_trip_request(session, user.id, body, settings, distance_fn)


@router.get("/api/trip-requests/{trip_id}", response_model=TripRequestOut)
def get_trip_request(
    trip_id: uuid.UUID, user: User = Depends(get_current_user), session: Session = Depends(get_db)
) -> TripRequestOut:
    trip = service.get_trip_request(session, trip_id)
    if trip is None:
        raise ApiError(404, "NOT_FOUND", "Resource not found")
    ensure_owner_or_admin(trip.user_id, user)
    return service.to_out(trip)
