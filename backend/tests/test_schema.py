"""P1.2 - Schema, Revision 9 Section 56.2 constraints/indexes, migrations,
pricing_configs seed and immutability."""

import uuid
from datetime import UTC, datetime, timedelta

import pytest
import yaml
from alembic import command
from sqlalchemy import Engine, create_engine, inspect, text
from sqlalchemy.exc import DBAPIError, IntegrityError
from sqlalchemy.orm import Session

from app.db.models import metadata
from app.modules.pricing.seed import (
    SERVICE_SECTIONS,
    PricingSeedConflict,
    canonical_sha256,
    seed_pricing_configs,
)
from tests.conftest import CONFIG_BASELINE, alembic_config, drop_database, recreate_database

pytestmark = pytest.mark.db

SECTION_56_1_TABLES = {
    "vehicles", "driver_profiles", "trip_requests", "ride_plans", "ride_candidates", "bookings",
    "ride_participants", "scheduled_trips", "seat_bookings", "driver_payouts", "fund_ledger",
}
SUPPORTING_TABLES = {
    "users", "refresh_tokens", "driver_locations", "service_areas", "pickup_points",
    "seat_holds", "idempotency_records", "scheduled_jobs", "pricing_configs",
    "survey_respondents", "survey_responses",
}

# --- minimal row factories (raw SQL keeps tests independent of services) -------


def make_user(s: Session, role: str = "PASSENGER") -> uuid.UUID:
    return s.execute(
        text("INSERT INTO users (email, password_hash, role) VALUES (:e, 'x', :r) RETURNING id"),
        {"e": f"{uuid.uuid4().hex}@example.com", "r": role},
    ).scalar_one()


def make_driver(s: Session, kyc: str = "VERIFIED") -> tuple[uuid.UUID, uuid.UUID]:
    uid = make_user(s, "DRIVER")
    s.execute(text("INSERT INTO driver_profiles (user_id, kyc_status) VALUES (:u, :k)"), {"u": uid, "k": kyc})
    vid = s.execute(
        text("INSERT INTO vehicles (driver_id, vehicle_type, license_plate, capacity) "
             "VALUES (:u, 'CAR4', :p, 4) RETURNING id"),
        {"u": uid, "p": uuid.uuid4().hex[:10]},
    ).scalar_one()
    return uid, vid


def make_trip_request(s: Session, user_id: uuid.UUID) -> uuid.UUID:
    return s.execute(
        text("""INSERT INTO trip_requests (user_id, mode, vehicle_preference, ride_preference,
                    allowed_service_codes, rejection_reasons_json, booking_type, passenger_count,
                    has_luggage, pickup_geom, dropoff_geom, preferred_departure, service_area_version)
                VALUES (:u, 'URBAN', 'ANY', 'ANY', ARRAY['CAR_URBAN_PRIVATE'], '[]', 'NOW', 1, false,
                    ST_SetSRID(ST_MakePoint(105.80, 21.00), 4326), ST_SetSRID(ST_MakePoint(105.85, 21.03), 4326),
                    now(), 'test') RETURNING id"""),
        {"u": user_id},
    ).scalar_one()


def make_booking(s: Session, **cols: object) -> uuid.UUID:
    uid = make_user(s)
    rid = make_trip_request(s, uid)
    values = {"request_id": rid, "user_id": uid, "service_code": "CAR_URBAN_POOL", "booking_type": "NOW"} | cols
    names = ", ".join(values)
    params = ", ".join(f":{k}" for k in values)
    return s.execute(text(f"INSERT INTO bookings ({names}) VALUES ({params}) RETURNING id"), values).scalar_one()


def assert_rejected(s: Session, constraint: str, sql: str, params: dict[str, object]) -> None:
    s.execute(text("SAVEPOINT sp"))
    with pytest.raises(IntegrityError) as exc:
        s.execute(text(sql), params)
    s.execute(text("ROLLBACK TO SAVEPOINT sp"))
    assert constraint in str(exc.value.orig), f"expected {constraint}, got {exc.value.orig}"


def accepted(s: Session, sql: str, params: dict[str, object]) -> None:
    s.execute(text(sql), params)


# --- migrations -----------------------------------------------------------------


def test_migration_from_empty_db_downgrade_and_reupgrade() -> None:
    name = "ridesharing_test_migrations"
    url = recreate_database(name)
    cfg = alembic_config(url)
    engine = create_engine(url)
    try:
        command.upgrade(cfg, "head")
        tables = set(inspect(engine).get_table_names())
        assert SECTION_56_1_TABLES | SUPPORTING_TABLES <= tables

        command.downgrade(cfg, "base")
        engine.dispose()
        left = set(inspect(engine).get_table_names()) - {"alembic_version", "spatial_ref_sys"}
        assert left == set(), f"downgrade left tables behind: {left}"
        with engine.connect() as conn:  # PostGIS intentionally kept
            assert conn.execute(text("SELECT count(*) FROM pg_extension WHERE extname='postgis'")).scalar() == 1

        command.upgrade(cfg, "head")
        engine.dispose()
        assert SECTION_56_1_TABLES | SUPPORTING_TABLES <= set(inspect(engine).get_table_names())
        command.check(cfg)  # models and migrated schema agree (no pending autogenerate diff)
    finally:
        engine.dispose()
        drop_database(name)


def test_models_cover_all_migrated_tables(db_engine: Engine) -> None:
    migrated = set(inspect(db_engine).get_table_names()) - {"alembic_version", "spatial_ref_sys"}
    assert migrated == set(metadata.tables)


# --- Section 56.2 indexes -------------------------------------------------------

REQUIRED_INDEXES = {
    # name: (table, fragments that must appear in pg_indexes.indexdef)
    "idx_driver_locations_geom": ("driver_locations", ["USING gist", "(geom)"]),
    "idx_service_areas_geom": ("service_areas", ["USING gist", "(geom)"]),
    "idx_pickup_points_geom": ("pickup_points", ["USING gist", "(geom)"]),
    "idx_scheduled_jobs_due": (
        "scheduled_jobs", ["(run_at)", "WHERE", "'PENDING'", "'FAILED_RETRY'"]),
    "idx_scheduled_trips_search": (
        "scheduled_trips", ["(corridor_id, departure_time)", "WHERE", "'OPEN_FOR_BOOKING'"]),
    "idx_active_hold_per_request": (
        "seat_holds", ["UNIQUE INDEX", "(request_id)", "WHERE", "'ACTIVE'"]),
    "uq_idempotency_records_user_id_idempotency_key": (
        "idempotency_records", ["UNIQUE INDEX", "(user_id, idempotency_key)"]),
    "uq_scheduled_jobs_idempotency_key": ("scheduled_jobs", ["UNIQUE INDEX", "(idempotency_key)"]),
}


@pytest.mark.parametrize("index_name", sorted(REQUIRED_INDEXES))
def test_required_index_exists(db_engine: Engine, index_name: str) -> None:
    table, fragments = REQUIRED_INDEXES[index_name]
    with db_engine.connect() as conn:
        row = conn.execute(
            text("SELECT tablename, indexdef FROM pg_indexes WHERE indexname = :n"), {"n": index_name}
        ).one_or_none()
    assert row is not None, f"missing index {index_name}"
    assert row.tablename == table
    for fragment in fragments:
        assert fragment in row.indexdef, f"{index_name}: '{fragment}' not in {row.indexdef}"


# --- Section 56.2 CHECK constraints -----------------------------------------------

TRIP_SQL = """INSERT INTO scheduled_trips (driver_id, vehicle_id, corridor_id, departure_time,
    seats_total, seats_booked, min_seats_ref, min_seats_to_run, seat_reference_vnd, seat_price_vnd)
    VALUES (:d, :v, 'HN-HY', now() + interval '5 days', :total, :booked, :ref, :run, :seat_ref, :price)"""


def _trip(d: uuid.UUID, v: uuid.UUID, **over: int) -> dict[str, object]:
    return {"d": d, "v": v, "total": 4, "booked": 0, "ref": 3, "run": 3, "seat_ref": 200000, "price": 200000} | over


def test_scheduled_trips_checks(db_session: Session) -> None:
    d, v = make_driver(db_session)
    accepted(db_session, TRIP_SQL, _trip(d, v))
    accepted(db_session, TRIP_SQL, _trip(d, v, run=2, price=180000))  # band edge 90%
    accepted(db_session, TRIP_SQL, _trip(d, v, price=220000))  # band edge 110%
    seats = "ck_scheduled_trips_seats_within_capacity"
    assert_rejected(db_session, seats, TRIP_SQL, _trip(d, v, booked=-1))
    assert_rejected(db_session, seats, TRIP_SQL, _trip(d, v, booked=5, total=4))
    assert_rejected(db_session, seats, TRIP_SQL, _trip(d, v, total=5, booked=0))
    rules = "ck_scheduled_trips_min_seats_rules"
    assert_rejected(db_session, rules, TRIP_SQL, _trip(d, v, run=4))
    assert_rejected(db_session, rules, TRIP_SQL, _trip(d, v, ref=2))
    band = "ck_scheduled_trips_seat_price_band"
    assert_rejected(db_session, band, TRIP_SQL, _trip(d, v, price=179999))
    assert_rejected(db_session, band, TRIP_SQL, _trip(d, v, price=220001))


PART_SQL = """INSERT INTO ride_participants (ride_plan_id, booking_id, floor_fare_vnd, cap_fare_vnd,
    fare_exact_vnd, fare_charged_vnd) VALUES (:p, :b, :floor, :cap, :exact, :charged)"""


def test_ride_participants_checks(db_session: Session) -> None:
    d, v = make_driver(db_session)
    plan = db_session.execute(
        text("INSERT INTO ride_plans (driver_id, vehicle_id, service_code) "
             "VALUES (:d, :v, 'CAR_URBAN_POOL') RETURNING id"), {"d": d, "v": v}
    ).scalar_one()

    def row(**over: object) -> dict[str, object]:
        return {"p": plan, "b": make_booking(db_session), "floor": 82000, "cap": 164000,
                "exact": 86666.67, "charged": 86000} | over

    accepted(db_session, PART_SQL, row())
    accepted(db_session, PART_SQL, row(exact=81999.99))  # tolerance 0.01 below floor
    exact = "ck_ride_participants_fare_exact_within_bounds"
    assert_rejected(db_session, exact, PART_SQL, row(exact=81999.98))
    assert_rejected(db_session, exact, PART_SQL, row(exact=164000.02))
    charged = "ck_ride_participants_fare_charged_within_cap"
    assert_rejected(db_session, charged, PART_SQL, row(charged=-1))
    assert_rejected(db_session, charged, PART_SQL, row(charged=164001))


def test_bookings_final_price_cap(db_session: Session) -> None:
    make_booking(db_session, quoted_price_cap_vnd=155000, final_price_vnd=155000)
    make_booking(db_session, quoted_price_cap_vnd=155000, final_price_vnd=None)
    make_booking(db_session, quoted_price_cap_vnd=200000, final_price_vnd=318000, price_status="TOPUP_LOCKED")
    db_session.execute(text("SAVEPOINT sp"))
    with pytest.raises(IntegrityError) as exc:
        make_booking(db_session, quoted_price_cap_vnd=155000, final_price_vnd=155001, price_status="MATCHED_LOCKED")
    db_session.execute(text("ROLLBACK TO SAVEPOINT sp"))
    assert "ck_bookings_final_price_within_cap" in str(exc.value.orig)


def test_unique_constraints(db_session: Session) -> None:
    uid = make_user(db_session)
    idem = "INSERT INTO idempotency_records (user_id, idempotency_key) VALUES (:u, :k)"
    accepted(db_session, idem, {"u": uid, "k": "key-1"})
    accepted(db_session, idem, {"u": make_user(db_session), "k": "key-1"})  # same key, other user
    assert_rejected(db_session, "uq_idempotency_records_user_id_idempotency_key", idem, {"u": uid, "k": "key-1"})

    job = ("INSERT INTO scheduled_jobs (job_type, target_id, run_at, idempotency_key) "
           "VALUES ('OFFER_TIMEOUT', gen_random_uuid(), now(), :k)")
    accepted(db_session, job, {"k": "job-1"})
    assert_rejected(db_session, "uq_scheduled_jobs_idempotency_key", job, {"k": "job-1"})


def test_seat_holds_one_active_hold_per_request(db_session: Session) -> None:
    rid = make_trip_request(db_session, make_user(db_session))
    hold = "INSERT INTO seat_holds (request_id, status, expires_at) VALUES (:r, :s, now() + interval '35 seconds')"
    accepted(db_session, hold, {"r": rid, "s": "ACTIVE"})
    accepted(db_session, hold, {"r": rid, "s": "RELEASED"})  # non-active holds are unrestricted
    assert_rejected(db_session, "idx_active_hold_per_request", hold, {"r": rid, "s": "ACTIVE"})


def test_vehicle_capacity_and_kyc_gate(db_session: Session) -> None:
    uid = make_user(db_session, "DRIVER")
    db_session.execute(text("INSERT INTO driver_profiles (user_id) VALUES (:u)"), {"u": uid})
    veh = "INSERT INTO vehicles (driver_id, vehicle_type, license_plate, capacity) VALUES (:u, :t, :p, :c)"
    assert_rejected(db_session, "ck_vehicles_capacity_matches_type", veh,
                    {"u": uid, "t": "BIKE", "p": "29A-1", "c": 2})
    assert_rejected(db_session, "ck_vehicles_capacity_matches_type", veh,
                    {"u": uid, "t": "CAR4", "p": "29A-2", "c": 1})
    gate = "UPDATE driver_profiles SET pool_enabled = true WHERE user_id = :u"
    assert_rejected(db_session, "ck_driver_profiles_kyc_gates_pool_and_intercity", gate, {"u": uid})


def test_gender_cannot_be_marked_verified(db_session: Session) -> None:
    uid = make_user(db_session)
    assert_rejected(db_session, "ck_users_gender_verification_status",
                    "UPDATE users SET gender_verification_status = 'VERIFIED' WHERE id = :u", {"u": uid})


# --- pricing_configs (P1-D7) ------------------------------------------------------


@pytest.fixture()
def baseline() -> dict:
    return yaml.safe_load(CONFIG_BASELINE.read_text(encoding="utf-8"))


def test_pricing_seed_is_idempotent_and_traceable(db_session: Session, baseline: dict) -> None:
    first = seed_pricing_configs(db_session, baseline)
    second = seed_pricing_configs(db_session, baseline)
    assert sorted(first.inserted + first.unchanged) == sorted(SERVICE_SECTIONS)
    assert second.inserted == [] and sorted(second.unchanged) == sorted(SERVICE_SECTIONS)

    rows = db_session.execute(text(
        "SELECT * FROM pricing_configs WHERE version = 'price_v9_two_sided_bounded' ORDER BY service_code"
    )).mappings().all()
    assert len(rows) == 5
    for r in rows:
        assert r["config_baseline_version"] == "MVP_CONFIG_BASELINE_V1"
        assert r["source_sha256"] == canonical_sha256(baseline)
        for section in SERVICE_SECTIONS[r["service_code"]]:
            assert r["params_json"]["sections"][section] == baseline[section]


def test_pricing_seed_reports_insert_then_unchanged(db_session: Session, baseline: dict) -> None:
    """Regression: the first seed of a version must report `inserted` (a bug
    reported every row as `unchanged`). Uses a test-only version name because
    pricing_configs rows cannot be deleted between tests."""
    fresh = baseline | {"pricing_version": f"test_seed_{uuid.uuid4().hex[:8]}"}
    first = seed_pricing_configs(db_session, fresh)
    second = seed_pricing_configs(db_session, fresh)
    assert sorted(first.inserted) == sorted(SERVICE_SECTIONS) and first.unchanged == []
    assert second.inserted == [] and sorted(second.unchanged) == sorted(SERVICE_SECTIONS)


def test_pricing_seed_refuses_to_overwrite(db_session: Session, baseline: dict) -> None:
    seed_pricing_configs(db_session, baseline)
    tampered = baseline | {"car_urban": baseline["car_urban"] | {"d_max": 0.61}}
    with pytest.raises(PricingSeedConflict):
        seed_pricing_configs(db_session, tampered)
    stored = db_session.execute(
        text("SELECT params_json FROM pricing_configs "
             "WHERE version = 'price_v9_two_sided_bounded' AND service_code = 'CAR_URBAN_POOL'")
    ).scalar_one()
    assert stored["sections"]["car_urban"]["d_max"] == 0.60


@pytest.mark.parametrize(
    "statement",
    [
        "UPDATE pricing_configs SET active_from = now()",
        "DELETE FROM pricing_configs",
        "TRUNCATE pricing_configs",
    ],
)
def test_pricing_configs_are_immutable(db_session: Session, baseline: dict, statement: str) -> None:
    seed_pricing_configs(db_session, baseline)
    with pytest.raises(DBAPIError) as exc:
        db_session.execute(text(statement))
    db_session.rollback()
    assert "immutable" in str(exc.value.orig)


def test_pricing_insert_new_version_is_allowed(db_session: Session, baseline: dict) -> None:
    """Immutability blocks changes, not new versions (Baseline Section 5.1)."""
    seed_pricing_configs(db_session, baseline)
    db_session.execute(text(
        "INSERT INTO pricing_configs (version, service_code, params_json, active_from, "
        "config_baseline_version, source_sha256) VALUES ('test_only_version', 'BIKE_URBAN', '{}', :t, 'X', 'Y')"
    ), {"t": datetime.now(UTC) + timedelta(days=1)})
    db_session.rollback()  # never persisted
