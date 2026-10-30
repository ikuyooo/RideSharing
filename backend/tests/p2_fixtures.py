"""SYNTHETIC P2 data written straight into a throwaway database (tests and the P2
benchmark): service area, pricing seed, drivers with vehicles and locations, trip
requests and open pool plans. Nothing here is real data."""

import uuid
from datetime import datetime, timedelta
from pathlib import Path

import yaml
from sqlalchemy import text
from sqlalchemy.orm import Session

REPO_ROOT = Path(__file__).resolve().parents[2]
VERSION = "synthetic-p2-areas"
# SYNTHETIC: TOTAL covers northern Vietnam roughly, URBAN a box around central Hà Nội.
TOTAL_WKT = "MULTIPOLYGON(((104.8 20.0,107.0 20.0,107.0 22.0,104.8 22.0,104.8 20.0)))"
URBAN_WKT = "MULTIPOLYGON(((105.70 20.90,105.95 20.90,105.95 21.15,105.70 21.15,105.70 20.90)))"
SERVICEABILITY = ('{"anchor": {"lon": 105.8542, "lat": 21.0285}, "max_road_km": 150.0, "max_snap_m": 300.0, '
                  '"exclude": ["ferry"]}')
URBAN = ["BIKE_URBAN", "CAR_URBAN_PRIVATE", "CAR_URBAN_POOL"]


def setup_reference_data(session: Session) -> None:
    from app.modules.pricing.seed import seed_pricing_configs

    for area_type, wkt in (("TOTAL", TOTAL_WKT), ("URBAN", URBAN_WKT)):
        session.execute(text(
            "INSERT INTO service_areas (area_type, service_area_version, status, geom, source_json, approved_at, "
            "approval_reference) VALUES (:t, :v, 'APPROVED', ST_GeomFromText(:w, 4326), CAST(:src AS jsonb), now(), "
            "'SYNTHETIC TEST DATA - not a real approval')"),
            {"t": area_type, "v": VERSION, "w": wkt,
             "src": '{"synthetic": true' + (', "serviceability": ' + SERVICEABILITY if area_type == "TOTAL" else "") + "}"})
    baseline = yaml.safe_load((REPO_ROOT / "config" / "mvp_config_baseline_v1.yaml").read_text(encoding="utf-8"))
    seed_pricing_configs(session, baseline)
    session.commit()


def user(session: Session, role: str = "PASSENGER") -> uuid.UUID:
    uid = uuid.uuid4()
    session.execute(text("INSERT INTO users (id, email, password_hash, role) VALUES (:i, :e, 'x', :r)"),
                    {"i": uid, "e": f"{role.lower()}-{uid.hex[:12]}@example.com", "r": role})
    return uid


def driver(session: Session, lon: float, lat: float, now: datetime, *, vehicle_type: str = "CAR4",
           availability: str = "IDLE", pool: bool = False, kyc: str | None = None, age_s: float = 5,
           max_additional_pickups: int = 0, accepts_urban: bool = True, detour_km: float | None = None,
           detour_min: float | None = None) -> tuple[uuid.UUID, uuid.UUID]:
    did = user(session, "DRIVER")
    kyc = kyc or ("VERIFIED" if pool else "NONE")
    session.execute(text(
        "INSERT INTO driver_profiles (user_id, kyc_status, accepts_urban, pool_enabled, max_additional_pickups, "
        "max_driver_detour_km, max_driver_detour_min) VALUES (:d, :k, :u, :p, :m, :dk, :dm)"),
        {"d": did, "k": kyc, "u": accepts_urban, "p": pool, "m": max_additional_pickups, "dk": detour_km,
         "dm": detour_min})
    vid = uuid.uuid4()
    session.execute(text("INSERT INTO vehicles (id, driver_id, vehicle_type, license_plate, capacity) "
                         "VALUES (:v, :d, :t, :lp, :c)"),
                    {"v": vid, "d": did, "t": vehicle_type, "lp": f"T-{vid.hex[:10]}", "c": 1 if vehicle_type == "BIKE" else 4})
    session.execute(text(
        "INSERT INTO driver_locations (driver_id, geom, updated_at, availability, active_vehicle_id) "
        "VALUES (:d, ST_SetSRID(ST_MakePoint(:lon, :lat), 4326), :u, :a, :v)"),
        {"d": did, "lon": lon, "lat": lat, "u": now - timedelta(seconds=age_s), "a": availability,
         "v": None if availability == "OFFLINE" else vid})
    return did, vid


def trip(session: Session, rider: uuid.UUID, pickup: tuple[float, float], dropoff: tuple[float, float],
         created: datetime, *, booking_type: str = "NOW", preferred: datetime | None = None, passengers: int = 1,
         allowed: list[str] | None = None, budget_max: int | None = None, same_gender: bool = False,
         latest_arrival: datetime | None = None) -> uuid.UUID:
    tid = uuid.uuid4()
    session.execute(text(
        "INSERT INTO trip_requests (id, user_id, mode, vehicle_preference, ride_preference, allowed_service_codes, "
        "rejection_reasons_json, booking_type, passenger_count, has_luggage, pickup_geom, dropoff_geom, "
        "preferred_departure, latest_arrival, budget_max, categorical_preferences_json, service_area_version, "
        "created_at) VALUES (:i, :u, 'URBAN', 'ANY', 'ANY', :a, '[]', :bt, :pc, false, "
        "ST_SetSRID(ST_MakePoint(:plon, :plat), 4326), ST_SetSRID(ST_MakePoint(:dlon, :dlat), 4326), :pref, :la, "
        ":b, CAST(:prefs AS jsonb), :v, :c)"),
        {"i": tid, "u": rider, "a": allowed or URBAN, "bt": booking_type, "pc": passengers, "plon": pickup[0],
         "plat": pickup[1], "dlon": dropoff[0], "dlat": dropoff[1], "pref": preferred or created, "la": latest_arrival,
         "b": budget_max, "prefs": '{"same_gender_coride": %s}' % ("true" if same_gender else "false"), "v": VERSION,
         "c": created})
    return tid


def onboard_plan(session: Session, driver_id: uuid.UUID, vehicle_id: uuid.UUID, rider_trip: uuid.UUID,
                 rider: uuid.UUID, pickup: tuple[float, float], dropoff: tuple[float, float], boarded: datetime,
                 *, direct_m: float, direct_s: float, traveled_km: float, cap_vnd: int) -> uuid.UUID:
    """An open plan with one rider already on board (pickup COMPLETED, dropoff ahead)."""
    plan, booking = uuid.uuid4(), uuid.uuid4()
    session.execute(text("INSERT INTO ride_plans (id, driver_id, vehicle_id, service_code, status, completed_stop_index, "
                         "plan_version) VALUES (:p, :d, :v, 'CAR_URBAN_POOL', 'PLAN_OPEN_SEARCHING', 0, 3)"),
                    {"p": plan, "d": driver_id, "v": vehicle_id})
    session.execute(text("INSERT INTO bookings (id, request_id, user_id, driver_id, service_code, booking_type, "
                         "seat_count, ride_plan_id, ride_status, price_status, quoted_price_cap_vnd) VALUES "
                         "(:b, :r, :u, :d, 'CAR_URBAN_POOL', 'NOW', 1, :p, 'RIDE_STARTED', 'POOL_SEARCHING', :cap)"),
                    {"b": booking, "r": rider_trip, "u": rider, "d": driver_id, "p": plan, "cap": cap_vnd})
    session.execute(text("INSERT INTO ride_participants (ride_plan_id, booking_id, seat_count, "
                         "traveled_km_before_last_replan, direct_distance_m, direct_duration_s) "
                         "VALUES (:p, :b, 1, :km, :dm, :ds)"),
                    {"p": plan, "b": booking, "km": traveled_km, "dm": direct_m, "ds": direct_s})
    for seq, kind, pt, status, done in ((0, "PICKUP", pickup, "COMPLETED", boarded),
                                        (1, "DROPOFF", dropoff, "PLANNED", None)):
        session.execute(text("INSERT INTO ride_stops (ride_plan_id, seq, kind, booking_id, geom, status, completed_at) "
                             "VALUES (:p, :s, :k, :b, ST_SetSRID(ST_MakePoint(:lon, :lat), 4326), :st, :c)"),
                        {"p": plan, "s": seq, "k": kind, "b": booking, "lon": pt[0], "lat": pt[1], "st": status, "c": done})
    session.execute(text("UPDATE driver_locations SET availability = 'BUSY' WHERE driver_id = :d"), {"d": driver_id})
    return plan
