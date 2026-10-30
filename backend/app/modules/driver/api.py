"""Driver endpoints. `PUT /api/driver/settings`, `PUT /api/driver/location` and
`POST /api/admin/drivers/{id}/kyc-review` are listed in Revision 9 Section 57.
`GET /api/driver/profile`, `POST /api/driver/vehicles` and
`POST /api/driver/kyc/submit` are TECHNICAL ADDITIONS needed by the Section 81
flow ("tài xế ... gửi thông tin giấy phép lái xe / đăng ký xe giả lập").
`PUT /api/driver/availability` is a Phase 2 TECHNICAL ADDITION (hard constraint 1:
"online, IDLE, right vehicle type")."""

import uuid

from fastapi import APIRouter, Depends, Response, status
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.modules.driver import service
from app.modules.driver.models import DriverProfile, Vehicle
from app.modules.driver.schemas import (
    AvailabilityIn,
    DriverProfileOut,
    DriverSettingsIn,
    KycReviewIn,
    KycSubmitIn,
    LocationIn,
    VehicleIn,
    VehicleOut,
)
from app.modules.identity.deps import User, require_roles

router = APIRouter(tags=["driver"])
driver_only = require_roles("DRIVER")
admin_only = require_roles("ADMIN")


def _profile_out(session: Session, profile: DriverProfile) -> DriverProfileOut:
    out = DriverProfileOut.model_validate(profile)
    out.vehicles = [VehicleOut.model_validate(v) for v in service.list_vehicles(session, profile.user_id)]
    return out


@router.get("/api/driver/profile", response_model=DriverProfileOut)
def get_profile(user: User = Depends(driver_only), session: Session = Depends(get_db)) -> DriverProfileOut:
    return _profile_out(session, service.ensure_profile(session, user.id))


@router.post("/api/driver/vehicles", response_model=VehicleOut, status_code=status.HTTP_201_CREATED)
def add_vehicle(body: VehicleIn, user: User = Depends(driver_only), session: Session = Depends(get_db)) -> Vehicle:
    return service.add_vehicle(session, user.id, body.vehicle_type, body.license_plate)


@router.post("/api/driver/kyc/submit", response_model=DriverProfileOut)
def submit_kyc(body: KycSubmitIn, user: User = Depends(driver_only), session: Session = Depends(get_db)) -> DriverProfileOut:
    return _profile_out(session, service.submit_kyc(session, user.id, body.model_dump()))


@router.put("/api/driver/settings", response_model=DriverProfileOut)
def update_settings(
    body: DriverSettingsIn, user: User = Depends(driver_only), session: Session = Depends(get_db)
) -> DriverProfileOut:
    return _profile_out(session, service.update_settings(session, user.id, body))


@router.put("/api/driver/location", status_code=status.HTTP_204_NO_CONTENT)
def update_location(body: LocationIn, user: User = Depends(driver_only), session: Session = Depends(get_db)) -> Response:
    service.update_location(session, user.id, body.lat, body.lon)
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.put("/api/driver/availability", status_code=status.HTTP_204_NO_CONTENT)
def update_availability(body: AvailabilityIn, user: User = Depends(driver_only),
                        session: Session = Depends(get_db)) -> Response:
    service.set_availability(session, user.id, body.availability, body.vehicle_id)
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.post("/api/admin/drivers/{driver_id}/kyc-review", response_model=DriverProfileOut)
def kyc_review(
    driver_id: uuid.UUID, body: KycReviewIn, admin: User = Depends(admin_only), session: Session = Depends(get_db)
) -> DriverProfileOut:
    return _profile_out(session, service.review_kyc(session, driver_id, body.decision, admin.id))
