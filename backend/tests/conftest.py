"""Shared fixtures.

Database tests run against a throwaway database (`ridesharing_test`) created on
the compose PostgreSQL/PostGIS instance and migrated with Alembic. They are
skipped - with the reason reported - when that server is not reachable.
Connection details come from TEST_PG_ADMIN_URL or the repository `.env`.
"""

import os
import uuid
from collections.abc import Iterator
from pathlib import Path

import pytest
from alembic import command
from alembic.config import Config
from sqlalchemy import Engine, create_engine, text
from sqlalchemy.engine import make_url
from sqlalchemy.orm import Session, sessionmaker

BACKEND_ROOT = Path(__file__).resolve().parents[1]
REPO_ROOT = BACKEND_ROOT.parent
TEST_DB_NAME = "ridesharing_test"
CONFIG_BASELINE = REPO_ROOT / "config" / "mvp_config_baseline_v1.yaml"

# Tables the tests may wipe between cases. pricing_configs is excluded: it is
# immutable by design (TRUNCATE is blocked by a trigger).
MUTABLE_TABLES = (
    "seat_bookings", "ride_stops", "ride_participants", "fund_ledger", "driver_payouts", "ride_candidates",
    "candidate_runs",
    "bookings", "seat_holds", "scheduled_trips", "ride_plans", "vehicles", "driver_locations",
    "trip_requests", "idempotency_records", "refresh_tokens", "driver_profiles", "users",
    "scheduled_jobs", "service_areas", "pickup_points", "survey_responses", "survey_respondents",
)
QUESTIONNAIRE = REPO_ROOT / "survey" / "s1" / "questionnaire.draft.yaml"


def _dotenv() -> dict[str, str]:
    env: dict[str, str] = {}
    path = REPO_ROOT / ".env"
    if path.is_file():
        for line in path.read_text(encoding="utf-8").splitlines():
            if "=" in line and not line.lstrip().startswith("#"):
                key, value = line.split("=", 1)
                env[key.strip()] = value.strip()
    return env


def admin_url() -> str:
    if url := os.environ.get("TEST_PG_ADMIN_URL"):
        return url
    env = _dotenv()
    user = env.get("POSTGRES_USER", "ridesharing")
    password = env.get("POSTGRES_PASSWORD", "")
    port = env.get("POSTGRES_HOST_PORT", "5432")
    return f"postgresql+psycopg://{user}:{password}@127.0.0.1:{port}/postgres"


def database_url(name: str) -> str:
    return make_url(admin_url()).set(database=name).render_as_string(hide_password=False)


def recreate_database(name: str) -> str:
    try:
        engine = create_engine(admin_url(), isolation_level="AUTOCOMMIT")
        with engine.connect() as conn:
            conn.execute(text(f'DROP DATABASE IF EXISTS "{name}" WITH (FORCE)'))
            conn.execute(text(f'CREATE DATABASE "{name}"'))
        engine.dispose()
    except Exception as exc:  # noqa: BLE001
        pytest.skip(f"PostgreSQL test server not reachable: {type(exc).__name__}: {exc}")
    return database_url(name)


def drop_database(name: str) -> None:
    engine = create_engine(admin_url(), isolation_level="AUTOCOMMIT")
    with engine.connect() as conn:
        conn.execute(text(f'DROP DATABASE IF EXISTS "{name}" WITH (FORCE)'))
    engine.dispose()


def alembic_config(url: str) -> Config:
    cfg = Config(str(BACKEND_ROOT / "alembic.ini"))
    cfg.set_main_option("script_location", str(BACKEND_ROOT / "alembic"))
    cfg.attributes["database_url"] = url
    return cfg


@pytest.fixture(scope="session")
def migrated_db_url() -> Iterator[str]:
    url = recreate_database(TEST_DB_NAME)
    command.upgrade(alembic_config(url), "head")
    yield url
    drop_database(TEST_DB_NAME)


@pytest.fixture(scope="session")
def db_engine(migrated_db_url: str) -> Iterator[Engine]:
    engine = create_engine(migrated_db_url)
    yield engine
    engine.dispose()


@pytest.fixture()
def db_session(db_engine: Engine) -> Iterator[Session]:
    session = sessionmaker(bind=db_engine, expire_on_commit=False)()
    try:
        yield session
    finally:
        session.rollback()
        session.close()
        with db_engine.begin() as conn:
            conn.execute(text(f"TRUNCATE {', '.join(MUTABLE_TABLES)} RESTART IDENTITY CASCADE"))


@pytest.fixture()
def app_env(monkeypatch: pytest.MonkeyPatch, migrated_db_url: str) -> None:
    """Environment for building the FastAPI app against the test database."""
    monkeypatch.setenv("DATABASE_URL", migrated_db_url)
    monkeypatch.setenv("REDIS_URL", "redis://127.0.0.1:1/0")
    monkeypatch.setenv("OSRM_CAR_URL", "http://127.0.0.1:1")
    monkeypatch.setenv("OSRM_MOTORBIKE_URL", "http://127.0.0.1:1")
    monkeypatch.setenv("CONFIG_BASELINE_PATH", str(CONFIG_BASELINE))
    monkeypatch.setenv("JWT_SECRET", "test-secret-" + uuid.uuid4().hex)
    monkeypatch.setenv("SURVEY_S1_QUESTIONNAIRE_PATH", str(QUESTIONNAIRE))
    monkeypatch.setenv("SURVEY_DATASET", "TEST")
    monkeypatch.setenv("SURVEY_S1_RELEASED", "false")
    from app.core.settings import get_settings
    from app.db.session import get_engine, get_sessionmaker

    get_settings.cache_clear()
    get_engine.cache_clear()
    get_sessionmaker.cache_clear()
