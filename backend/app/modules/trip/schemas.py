import uuid
from datetime import datetime
from typing import Any, Literal

from pydantic import BaseModel, Field, model_validator


class Point(BaseModel):
    lat: float = Field(ge=-90, le=90)
    lon: float = Field(ge=-180, le=180)


class TripRequestIn(BaseModel):
    """Trip Intent R (Revision 9, Section 6)."""

    pickup: Point
    dropoff: Point
    vehicle_preference: Literal["BIKE", "CAR", "ANY"] = "ANY"
    ride_preference: Literal["PRIVATE", "POOL", "ANY"] = "ANY"
    passenger_count: int = Field(default=1, ge=1, le=4)
    has_luggage: bool = False
    booking_type: Literal["NOW", "SCHEDULED"] = "NOW"
    # Required for SCHEDULED; ignored for NOW (the server clock is used).
    preferred_departure: datetime | None = None
    earliest_departure: datetime | None = None
    latest_departure: datetime | None = None
    latest_arrival: datetime | None = None
    budget_min: int | None = Field(default=None, ge=0)
    budget_max: int | None = Field(default=None, ge=0)
    max_passenger_detour_ratio: float | None = Field(default=None, ge=0, le=1)
    max_in_vehicle_time_s: int | None = Field(default=None, gt=0)
    max_walk_m: int | None = Field(default=None, ge=0)
    categorical_preferences: dict[str, Any] | None = None

    @model_validator(mode="after")
    def _consistency(self) -> "TripRequestIn":
        if self.pickup == self.dropoff:
            raise ValueError("pickup and dropoff must differ")
        if self.booking_type == "SCHEDULED" and self.preferred_departure is None:
            raise ValueError("preferred_departure is required for SCHEDULED requests")
        for name in ("preferred_departure", "earliest_departure", "latest_departure", "latest_arrival"):
            value = getattr(self, name)
            if value is not None and value.tzinfo is None:
                raise ValueError(f"{name} must include a timezone offset")
        if self.budget_min is not None and self.budget_max is not None and self.budget_min > self.budget_max:
            raise ValueError("budget_min must not exceed budget_max")
        return self


class TripRequestOut(BaseModel):
    id: uuid.UUID
    mode: str
    booking_type: str
    preferred_departure: datetime
    allowed_service_codes: list[str]
    rejection_reasons: list[dict[str, Any]]
    direct_distance_km: float | None
    service_area_version: str
    created_at: datetime
