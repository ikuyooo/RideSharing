"""P1.5 - Trip Intent API behaviour.

Uses SYNTHETIC service areas (two squares, inserted only into the throwaway
test database) and an injected distance function. These tests prove the API
and error handling - NOT that any real geometry is correct or approved; the
real candidate geometry is evaluated separately and awaits owner approval."""

import logging
from collections.abc import Iterator
from datetime import UTC, datetime, timedelta

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import text
from sqlalchemy.orm import Session

from app.modules.routing.service import RouteNotFound, RoutingUnavailable
from tests.api_helpers import client, new_admin, new_user  # noqa: F401

pytestmark = pytest.mark.db

VERSION = "synthetic-test-areas"
# TOTAL square 105.0..106.0 x 20.0..21.5 ; URBAN square 105.7..105.9 x 20.9..21.1 (SYNTHETIC)
TOTAL_WKT = "MULTIPOLYGON(((105 20,106 20,106 21.5,105 21.5,105 20)))"
URBAN_WKT = "MULTIPOLYGON(((105.7 20.9,105.9 20.9,105.9 21.1,105.7 21.1,105.7 20.9)))"
URBAN_A = {"lat": 21.0, "lon": 105.8}
URBAN_B = {"lat": 21.05, "lon": 105.85}
OUTSIDE_URBAN = {"lat": 20.5, "lon": 105.5}
OUTSIDE_URBAN_2 = {"lat": 20.6, "lon": 105.4}
OUTSIDE_TOTAL = {"lat": 22.0, "lon": 107.0}


class FakeDistance:
    def __init__(self) -> None:
        self.km: float = 10.0
        self.error: Exception | None = None
        self.calls = 0

    def __call__(self, a: tuple[float, float], b: tuple[float, float]) -> float:
        self.calls += 1
        if self.error:
            raise self.error
        return self.km


@pytest.fixture()
def areas(db_session: Session) -> None:
    for area_type, wkt in (("TOTAL", TOTAL_WKT), ("URBAN", URBAN_WKT)):
        db_session.execute(text(
            "INSERT INTO service_areas (area_type, service_area_version, status, geom, source_json, approved_at, "
            "approval_reference) VALUES (:t, :v, 'APPROVED', ST_GeomFromText(:w, 4326), "
            "'{\"synthetic\": true}', now(), 'SYNTHETIC TEST DATA - not a real approval')"),
            {"t": area_type, "v": VERSION, "w": wkt})
    db_session.commit()


@pytest.fixture()
def fake_distance(client: TestClient, monkeypatch: pytest.MonkeyPatch, areas: None) -> Iterator[FakeDistance]:
    from app.core.settings import get_settings
    from app.modules.trip.api import get_distance_fn

    monkeypatch.setenv("SERVICE_AREA_VERSION", VERSION)
    get_settings.cache_clear()
    fake = FakeDistance()
    client.app.dependency_overrides[get_distance_fn] = lambda: fake
    yield fake
    client.app.dependency_overrides.clear()


def post(client: TestClient, headers: dict, **body: object) -> object:
    payload = {"pickup": URBAN_A, "dropoff": URBAN_B} | body
    return client.post("/api/trip-requests", json=payload, headers=headers)


def test_both_urban_is_urban_without_routing(client: TestClient, fake_distance: FakeDistance) -> None:
    _, headers = new_user(client)
    resp = post(client, headers)
    assert resp.status_code == 201, resp.text
    body = resp.json()
    assert body["mode"] == "URBAN" and fake_distance.calls == 0
    assert body["allowed_service_codes"] == ["BIKE_URBAN", "CAR_URBAN_PRIVATE", "CAR_URBAN_POOL"]
    assert body["service_area_version"] == VERSION


@pytest.mark.parametrize("km,mode", [(15.0, "URBAN"), (15.01, "INTERCITY")])
def test_buffer_boundary_through_api(client: TestClient, fake_distance: FakeDistance, km: float, mode: str) -> None:
    _, headers = new_user(client)
    fake_distance.km = km
    resp = post(client, headers, dropoff=OUTSIDE_URBAN)
    assert resp.status_code == 201 and resp.json()["mode"] == mode
    assert resp.json()["direct_distance_km"] == km


def test_out_of_service_area_and_unsupported(client: TestClient, fake_distance: FakeDistance) -> None:
    _, headers = new_user(client)
    out = post(client, headers, dropoff=OUTSIDE_TOTAL)
    assert out.status_code == 422 and out.json()["error"]["code"] == "OUT_OF_SERVICE_AREA"
    both_outside = post(client, headers, pickup=OUTSIDE_URBAN, dropoff=OUTSIDE_URBAN_2)
    assert both_outside.json()["error"]["code"] == "UNSUPPORTED_INTER_PROVINCE_ROUTE"
    assert fake_distance.calls == 0


def test_routing_errors_are_explicit_no_fallback(client: TestClient, fake_distance: FakeDistance) -> None:
    _, headers = new_user(client)
    fake_distance.error = RouteNotFound("NoRoute")
    resp = post(client, headers, dropoff=OUTSIDE_URBAN)
    assert resp.status_code == 422 and resp.json()["error"]["code"] == "ROUTE_NOT_FOUND"
    fake_distance.error = RoutingUnavailable("down")
    resp = post(client, headers, dropoff=OUTSIDE_URBAN)
    assert resp.status_code == 503 and resp.json()["error"]["code"] == "ROUTING_UNAVAILABLE"


def test_scheduled_intercity_pool_window(client: TestClient, fake_distance: FakeDistance) -> None:
    _, headers = new_user(client)
    fake_distance.km = 60.0
    soon = (datetime.now(UTC) + timedelta(hours=48)).isoformat()
    resp = post(client, headers, dropoff=OUTSIDE_URBAN, booking_type="SCHEDULED", preferred_departure=soon)
    body = resp.json()
    assert body["mode"] == "INTERCITY" and body["allowed_service_codes"] == ["CAR_INTERCITY_PRIVATE"]
    pool = next(r for r in body["rejection_reasons"] if r["service_code"] == "CAR_INTERCITY_POOL")
    assert pool["details"]["suggested_service_code"] == "CAR_INTERCITY_PRIVATE"
    later = (datetime.now(UTC) + timedelta(days=4)).isoformat()
    body = post(client, headers, dropoff=OUTSIDE_URBAN, booking_type="SCHEDULED", preferred_departure=later).json()
    assert body["allowed_service_codes"] == ["CAR_INTERCITY_PRIVATE", "CAR_INTERCITY_POOL"]


def test_input_validation(client: TestClient, fake_distance: FakeDistance) -> None:
    _, headers = new_user(client)
    past = (datetime.now(UTC) - timedelta(minutes=5)).isoformat()
    assert post(client, headers, booking_type="SCHEDULED", preferred_departure=past).json()["error"]["code"] == \
        "DEPARTURE_IN_PAST"
    assert post(client, headers, booking_type="SCHEDULED").status_code == 422
    assert post(client, headers, dropoff=URBAN_A).status_code == 422
    assert post(client, headers, pickup={"lat": 95, "lon": 105}).status_code == 422
    assert post(client, headers, passenger_count=5).status_code == 422
    assert post(client, headers, budget_min=200000, budget_max=100000).status_code == 422


def test_only_passengers_create_and_owners_read(client: TestClient, fake_distance: FakeDistance,
                                                db_session: Session) -> None:
    _, owner = new_user(client)
    _, other = new_user(client)
    _, driver = new_user(client, "DRIVER")
    _, admin = new_admin(client, db_session)
    assert post(client, driver).status_code == 403
    trip_id = post(client, owner).json()["id"]
    assert client.get(f"/api/trip-requests/{trip_id}", headers=owner).status_code == 200
    assert client.get(f"/api/trip-requests/{trip_id}", headers=other).status_code == 404
    assert client.get(f"/api/trip-requests/{trip_id}", headers=admin).status_code == 200


def test_service_area_gates(client: TestClient, db_session: Session, monkeypatch: pytest.MonkeyPatch,
                            fake_distance: FakeDistance) -> None:
    from app.core.settings import get_settings

    _, headers = new_user(client)
    monkeypatch.setenv("SERVICE_AREA_VERSION", "")
    get_settings.cache_clear()
    assert post(client, headers).json()["error"]["code"] == "SERVICE_AREA_NOT_CONFIGURED"

    db_session.execute(text("UPDATE service_areas SET status = 'CANDIDATE', approved_at = NULL "
                            "WHERE service_area_version = :v"), {"v": VERSION})
    db_session.commit()
    monkeypatch.setenv("SERVICE_AREA_VERSION", VERSION)
    get_settings.cache_clear()
    assert post(client, headers).json()["error"]["code"] == "SERVICE_AREA_NOT_APPROVED"
    monkeypatch.setenv("ALLOW_CANDIDATE_SERVICE_AREA", "true")
    get_settings.cache_clear()
    assert post(client, headers).status_code == 201


def test_trip_coordinates_not_logged(client: TestClient, fake_distance: FakeDistance,
                                     caplog: pytest.LogCaptureFixture) -> None:
    _, headers = new_user(client)
    caplog.set_level(logging.DEBUG)
    precise = {"lat": 21.012345, "lon": 105.812345}
    assert post(client, headers, pickup=precise).status_code == 201
    assert "21.0123" not in caplog.text and "105.8123" not in caplog.text
