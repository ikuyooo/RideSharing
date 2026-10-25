"""Pure Trip Intent rules (no I/O): spatial classification (Revision 9
Section 2.3) and allowed-service derivation with booking-time rules (Sections
2.2 and 6). Every threshold comes from the locked baseline; nothing is hardcoded."""

from collections.abc import Callable, Mapping
from dataclasses import dataclass, field
from datetime import timedelta
from typing import Any

URBAN_SERVICES = ("BIKE_URBAN", "CAR_URBAN_PRIVATE", "CAR_URBAN_POOL")
INTERCITY_SERVICES = ("CAR_INTERCITY_PRIVATE", "CAR_INTERCITY_POOL")


# --- Section 2.3: URBAN / INTERCITY classification --------------------------------


@dataclass(frozen=True)
class Classification:
    mode: str | None  # URBAN | INTERCITY | None when rejected
    error_code: str | None  # OUT_OF_SERVICE_AREA | UNSUPPORTED_INTER_PROVINCE_ROUTE
    step: str
    direct_distance_km: float | None = None


def classify(
    pickup_in_total: bool,
    dropoff_in_total: bool,
    pickup_in_urban: bool,
    dropoff_in_urban: bool,
    road_distance_km: Callable[[], float],
    urban_boundary_buffer_km: float,
) -> Classification:
    """Three-step algorithm of Section 2.3. `road_distance_km` (OSRM car road
    distance, owner decision P1-D2) is only called when exactly one end is
    urban; its errors propagate to the caller."""
    # Step 1
    if not (pickup_in_total and dropoff_in_total):
        return Classification(None, "OUT_OF_SERVICE_AREA", "1")
    # Step 2
    if pickup_in_urban and dropoff_in_urban:
        return Classification("URBAN", None, "2a")
    if pickup_in_urban or dropoff_in_urban:
        distance = road_distance_km()
        if distance <= urban_boundary_buffer_km:
            return Classification("URBAN", None, "2b", distance)
        # Step 3
        return Classification("INTERCITY", None, "3a", distance)
    # Step 3, both ends outside the urban area
    return Classification(None, "UNSUPPORTED_INTER_PROVINCE_ROUTE", "3b")


# --- Section 6: allowed_service_codes ------------------------------------------------


@dataclass(frozen=True)
class Rejection:
    service_code: str
    code: str
    message_vi: str
    details: dict[str, Any] = field(default_factory=dict)

    def as_json(self) -> dict[str, Any]:
        return {"service_code": self.service_code, "code": self.code, "message_vi": self.message_vi} | (
            {"details": self.details} if self.details else {}
        )


@dataclass(frozen=True)
class ServiceWindow:
    """Allowed lead time ΔT = T_preferred - now, inclusive bounds."""

    min_lead: timedelta
    max_lead: timedelta


def service_windows(baseline: Mapping[str, Any]) -> dict[str, ServiceWindow]:
    """Section 2.2 / 6 lead-time windows from the baseline."""
    pool = baseline["car_intercity_pool"]
    return {
        "BIKE_URBAN": ServiceWindow(timedelta(0), timedelta(hours=baseline["bike_urban"]["max_ahead_hours"])),
        "CAR_URBAN_PRIVATE": ServiceWindow(timedelta(0), timedelta(hours=baseline["car_urban"]["max_ahead_hours"])),
        "CAR_URBAN_POOL": ServiceWindow(timedelta(0), timedelta(hours=baseline["car_urban"]["max_ahead_hours"])),
        "CAR_INTERCITY_PRIVATE": ServiceWindow(
            timedelta(0), timedelta(days=baseline["car_intercity_private"]["max_ahead_days"])
        ),
        "CAR_INTERCITY_POOL": ServiceWindow(
            timedelta(hours=pool["booking_close_hours"]), timedelta(days=pool["booking_open_days"])
        ),
    }


def max_passengers(baseline: Mapping[str, Any]) -> dict[str, int]:
    """Section 6 passenger limits: BIKE = bike capacity (1); CAR_URBAN_POOL =
    max_party_seats_pool (2); other CAR4 services = CAR4 capacity (4)."""
    car_capacity = int(baseline["car_urban"]["capacity"])
    return {
        "BIKE_URBAN": int(baseline["bike_urban"]["capacity"]),
        "CAR_URBAN_PRIVATE": car_capacity,
        "CAR_URBAN_POOL": int(baseline["car_urban"]["max_party_seats_pool"]),
        "CAR_INTERCITY_PRIVATE": car_capacity,
        "CAR_INTERCITY_POOL": car_capacity,
    }


VEHICLE_OF = {code: ("BIKE" if code == "BIKE_URBAN" else "CAR") for code in URBAN_SERVICES + INTERCITY_SERVICES}
RIDE_OF = {
    "BIKE_URBAN": "PRIVATE",
    "CAR_URBAN_PRIVATE": "PRIVATE",
    "CAR_URBAN_POOL": "POOL",
    "CAR_INTERCITY_PRIVATE": "PRIVATE",
    "CAR_INTERCITY_POOL": "POOL",
}
MODE_OF = {code: "URBAN" for code in URBAN_SERVICES} | {code: "INTERCITY" for code in INTERCITY_SERVICES}

_VEHICLE_VI = {"BIKE": "xe máy", "CAR": "ô tô"}


def _fmt(td: timedelta) -> str:
    hours = td.total_seconds() / 3600
    return f"{hours:g} giờ"


def _lead_time_ok(code: str, lead: timedelta, windows: Mapping[str, ServiceWindow]) -> bool:
    w = windows[code]
    return w.min_lead <= lead <= w.max_lead


def allowed_services(
    mode: str,
    vehicle_preference: str,
    ride_preference: str,
    passenger_count: int,
    has_luggage: bool,
    lead_time: timedelta,
    baseline: Mapping[str, Any],
) -> tuple[list[str], list[Rejection]]:
    """Section 6 necessary-and-sufficient table. Returns (allowed, rejections),
    one rejection (first failing condition) per excluded service."""
    windows = service_windows(baseline)
    limits = max_passengers(baseline)
    allowed: list[str] = []
    rejections: list[Rejection] = []
    for code in URBAN_SERVICES + INTERCITY_SERVICES:
        rejection: Rejection | None = None
        if MODE_OF[code] != mode:
            label = "nội đô" if MODE_OF[code] == "URBAN" else "liên tỉnh"
            rejection = Rejection(code, "MODE_MISMATCH", f"Dịch vụ chỉ phục vụ chuyến {label}.")
        elif vehicle_preference not in (VEHICLE_OF[code], "ANY"):
            rejection = Rejection(code, "VEHICLE_PREFERENCE_MISMATCH",
                                  f"Bạn đã chọn loại phương tiện khác {_VEHICLE_VI[VEHICLE_OF[code]]}.")
        elif ride_preference not in (RIDE_OF[code], "ANY"):
            rejection = Rejection(code, "RIDE_PREFERENCE_MISMATCH", "Bạn đã chọn hình thức đi khác.")
        elif not 1 <= passenger_count <= limits[code]:
            rejection = Rejection(code, "PASSENGER_COUNT_EXCEEDED",
                                  f"Dịch vụ nhận tối đa {limits[code]} khách mỗi lượt đặt.",
                                  {"max_passengers": limits[code], "passenger_count": passenger_count})
        elif code == "BIKE_URBAN" and has_luggage:
            rejection = Rejection(code, "LUGGAGE_NOT_ALLOWED", "Xe máy không khả dụng khi bạn mang hành lý lớn.")
        elif not _lead_time_ok(code, lead_time, windows):
            w = windows[code]
            details: dict[str, Any] = {
                "lead_time_s": int(lead_time.total_seconds()),
                "min_lead_s": int(w.min_lead.total_seconds()),
                "max_lead_s": int(w.max_lead.total_seconds()),
            }
            if code == "CAR_INTERCITY_POOL" and lead_time < w.min_lead:
                message = (f"Đi ghép liên tỉnh cần đặt trước tối thiểu {_fmt(w.min_lead)}; "
                           "bạn có thể chọn Taxi bao xe liên tỉnh để đi ngay.")
                # Section 6 / 72.2: suggest CAR_INTERCITY_PRIVATE when it would be valid.
                if passenger_count <= limits["CAR_INTERCITY_PRIVATE"] and _lead_time_ok(
                    "CAR_INTERCITY_PRIVATE", lead_time, windows
                ):
                    details["suggested_service_code"] = "CAR_INTERCITY_PRIVATE"
            else:
                message = f"Thời điểm khởi hành nằm ngoài khung đặt cho phép ({_fmt(w.min_lead)} – {_fmt(w.max_lead)})."
            rejection = Rejection(code, "LEAD_TIME_OUT_OF_WINDOW", message, details)
        if rejection is None:
            allowed.append(code)
        else:
            rejections.append(rejection)
    return allowed, rejections
