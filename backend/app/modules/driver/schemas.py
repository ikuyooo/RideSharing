import uuid
from datetime import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field


class VehicleIn(BaseModel):
    vehicle_type: Literal["BIKE", "CAR4"]
    license_plate: str = Field(min_length=4, max_length=20, pattern=r"^[0-9A-Za-z.\- ]+$")


class VehicleOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    vehicle_type: str
    license_plate: str
    capacity: int
    is_active: bool


class KycSubmitIn(BaseModel):
    """Section 81: mock driver licence / vehicle registration data. Not verified
    against any external system (eKYC is WON'T, Section 0.2)."""

    driving_licence_number: str = Field(min_length=4, max_length=32)
    driving_licence_class: str = Field(min_length=1, max_length=8)
    vehicle_registration_number: str = Field(min_length=4, max_length=32)


class DriverSettingsIn(BaseModel):
    """PUT /api/driver/settings (Section 57). Omitted fields are left unchanged."""

    accepts_urban: bool | None = None
    pool_enabled: bool | None = None
    accepts_intercity: bool | None = None
    max_additional_pickups: int | None = Field(default=None, ge=0, le=3)
    max_driver_detour_km: float | None = Field(default=None, ge=0)
    max_driver_detour_min: float | None = Field(default=None, ge=0)


class LocationIn(BaseModel):
    lat: float = Field(ge=-90, le=90)
    lon: float = Field(ge=-180, le=180)


class DriverProfileOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    user_id: uuid.UUID
    kyc_status: str
    accepts_urban: bool
    pool_enabled: bool
    accepts_intercity: bool
    max_additional_pickups: int
    max_driver_detour_km: float | None
    max_driver_detour_min: float | None
    kyc_submitted_at: datetime | None
    kyc_reviewed_at: datetime | None
    vehicles: list[VehicleOut] = []


class KycReviewIn(BaseModel):
    decision: Literal["VERIFIED", "REJECTED"]
