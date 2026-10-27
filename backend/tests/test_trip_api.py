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

from app.modules.routing.service import PointReach, Reachability, RouteNotFound, RoutingUnavailable
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
# SYNTHETIC tier-2 parameters (GEO-03) stored with the TOTAL row, as the build does.
SERVICEABILITY = '{"anchor": {"lon": 105.85, "lat": 21.03}, "max_road_km": 150.0, "max_snap_m": 300.0}'
# SYNTHETIC EXCLUDED square (an "island" without road) inside TOTAL, outside URBAN.
EXCLUDED_WKT = "MULTIPOLYGON(((105.2 20.2,105.3 20.2,105.3 20.3,105.2 20.3,105.2 20.2)))"
IN_EXCLUDED = {"lat": 20.25, "lon": 105.25}


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


class FakeReach:
    """Injected tier-2 OSRM /table answer (per-point snap / anchor distance)."""

    def __init__(self) -> None:
        self.pickup = PointReach(snap_m=10.0, anchor_road_km=20.0)
        self.dropoff = PointReach(snap_m=10.0, anchor_road_km=20.0)
        self.pickup_to_dropoff_km: float | None = 10.0
        self.error: Exception | None = None
        self.calls = 0

    def __call__(self, anchor: tuple[float, float], a: tuple[float, float], b: tuple[float, float]) -> Reachability:
        self.calls += 1
        assert anchor == (105.85, 21.03)
        if self.error:
            raise self.error
        return Reachability(self.pickup, self.dropoff, self.pickup_to_dropoff_km)


@pytest.fixture()
def areas(db_session: Session) -> None:
    for area_type, wkt in (("TOTAL", TOTAL_WKT), ("URBAN", URBAN_WKT)):
        db_session.execute(text(
            "INSERT INTO service_areas (area_type, service_area_version, status, geom, source_json, approved_at, "
            "approval_reference) VALUES (:t, :v, 'APPROVED', ST_GeomFromText(:w, 4326), "
            "CAST(:src AS jsonb), now(), 'SYNTHETIC TEST DATA - not a real approval')"),
            {"t": area_type, "v": VERSION, "w": wkt,
             "src": '{"synthetic": true' + (', "serviceability": ' + SERVICEABILITY if area_type == "TOTAL" else "") + "}"})
    db_session.commit()


@pytest.fixture()
def fake_distance(client: TestClient, monkeypatch: pytest.MonkeyPatch, areas: None) -> Iterator[FakeDistance]:
    from app.core.settings import get_settings
    from app.modules.trip.api import get_distance_fn, get_reach_fn

    monkeypatch.setenv("SERVICE_AREA_VERSION", VERSION)
    get_settings.cache_clear()
    fake = FakeDistance()
    fake.reach = FakeReach()  # type: ignore[attr-defined]
    client.app.dependency_overrides[get_distance_fn] = lambda: fake
    client.app.dependency_overrides[get_reach_fn] = lambda: fake.reach  # type: ignore[attr-defined]
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


def test_detour_ratio_spec_default_and_user_value(client: TestClient, fake_distance: FakeDistance,
                                                db_session: Session) -> None:
    """Owner decision A7: Revision 9 Section 6 default 0.30 when omitted (not a Baseline key)."""
    from app.modules.trip.rules import SPEC_DEFAULT_MAX_PASSENGER_DETOUR_RATIO

    assert SPEC_DEFAULT_MAX_PASSENGER_DETOUR_RATIO == 0.30
    _, headers = new_user(client)
    default = post(client, headers).json()
    assert default["max_passenger_detour_ratio"] == 0.30
    stored = db_session.execute(text("SELECT max_passenger_detour_ratio FROM trip_requests WHERE id = :i"),
                                {"i": default["id"]}).scalar_one()
    assert stored == 0.30
    assert post(client, headers, max_passenger_detour_ratio=0.25).json()["max_passenger_detour_ratio"] == 0.25
    for edge in (0, 1):
        assert post(client, headers, max_passenger_detour_ratio=edge).status_code == 201
    for bad in (-0.01, 1.01):
        assert post(client, headers, max_passenger_detour_ratio=bad).status_code == 422


def test_baseline_yaml_has_no_detour_ratio_key() -> None:
    """The default must not be silently added to the locked Baseline (A7)."""
    import yaml

    from tests.conftest import CONFIG_BASELINE

    assert "max_passenger_detour_ratio" not in CONFIG_BASELINE.read_text(encoding="utf-8")
    assert "max_passenger_detour_ratio" not in yaml.safe_load(CONFIG_BASELINE.read_text(encoding="utf-8"))["car_urban"]


def test_trip_coordinates_not_logged(client: TestClient, fake_distance: FakeDistance,
                                     caplog: pytest.LogCaptureFixture) -> None:
    _, headers = new_user(client)
    caplog.set_level(logging.DEBUG)
    precise = {"lat": 21.012345, "lon": 105.812345}
    assert post(client, headers, pickup=precise).status_code == 201
    assert "21.0123" not in caplog.text and "105.8123" not in caplog.text


# --- GEO-03 / GEO-04: two-tier service area -----------------------------------------------


def _error(resp: object) -> dict:
    assert resp.status_code == 422, resp.text  # type: ignore[attr-defined]
    return resp.json()["error"]  # type: ignore[attr-defined]


@pytest.mark.parametrize("km,ok", [(150.0, True), (150.001, False)])
def test_tier2_road_limit_exactly_150_accepted_beyond_rejected(client: TestClient, fake_distance: FakeDistance,
                                                               km: float, ok: bool) -> None:
    _, headers = new_user(client)
    fake_distance.km = 60.0
    fake_distance.reach.dropoff = PointReach(snap_m=5.0, anchor_road_km=km)  # type: ignore[attr-defined]
    resp = post(client, headers, dropoff=OUTSIDE_URBAN)
    if ok:
        assert resp.status_code == 201 and resp.json()["mode"] == "INTERCITY"
    else:
        err = _error(resp)
        assert err["code"] == "OUT_OF_SERVICE_AREA"
        assert err["details"]["dropoff"] == {"reason": "BEYOND_MAX_ROAD_DISTANCE", "layer": "SERVICEABILITY",
                                             "anchor_road_km": 150.001, "snap_m": 5.0}
        assert err["details"]["pickup"]["reason"] is None
        assert fake_distance.calls == 0  # rejected in step 1, no pickup-dropoff routing


@pytest.mark.parametrize("snap,reason", [(300.0, None), (300.1, "NO_ROAD_ACCESS")])
def test_tier2_snap_distance_limit(client: TestClient, fake_distance: FakeDistance, snap: float,
                                   reason: str | None) -> None:
    _, headers = new_user(client)
    fake_distance.reach.pickup = PointReach(snap_m=snap, anchor_road_km=5.0)  # type: ignore[attr-defined]
    resp = post(client, headers)
    if reason is None:
        assert resp.status_code == 201
    else:
        assert _error(resp)["details"]["pickup"]["reason"] == reason


def test_tier2_unroutable_points_and_routes(client: TestClient, fake_distance: FakeDistance) -> None:
    _, headers = new_user(client)
    reach = fake_distance.reach  # type: ignore[attr-defined]
    reach.dropoff = PointReach(snap_m=5.0, anchor_road_km=None)
    err = _error(post(client, headers, dropoff=OUTSIDE_URBAN))
    assert err["code"] == "OUT_OF_SERVICE_AREA" and err["details"]["dropoff"]["reason"] == "NOT_ROUTABLE_FROM_ANCHOR"

    reach.dropoff = PointReach(snap_m=5.0, anchor_road_km=40.0)
    reach.pickup_to_dropoff_km = None  # both points served, but nothing joins them
    assert _error(post(client, headers, dropoff=OUTSIDE_URBAN))["code"] == "ROUTE_NOT_FOUND"

    reach.error = RouteNotFound("NoSegment")  # OSRM could not snap at all
    err = _error(post(client, headers))
    assert err["details"]["pickup"]["reason"] == "NO_ROAD_ACCESS"

    reach.error = RoutingUnavailable("down")  # no fallback
    resp = post(client, headers)
    assert resp.status_code == 503 and resp.json()["error"]["code"] == "ROUTING_UNAVAILABLE"


def test_tier1_polygon_rejections_need_no_routing(client: TestClient, fake_distance: FakeDistance,
                                                  db_session: Session) -> None:
    _, headers = new_user(client)
    err = _error(post(client, headers, dropoff=OUTSIDE_TOTAL))
    assert err["details"]["dropoff"] == {"reason": "OUTSIDE_TOTAL_POLYGON", "layer": "POLYGON",
                                         "anchor_road_km": None, "snap_m": None}
    db_session.execute(text(
        "INSERT INTO service_areas (area_type, service_area_version, status, geom, source_json, approved_at, "
        "approval_reference) VALUES ('EXCLUDED', :v, 'APPROVED', ST_GeomFromText(:w, 4326), '{\"synthetic\": true}', "
        "now(), 'SYNTHETIC TEST DATA')"), {"v": VERSION, "w": EXCLUDED_WKT})
    db_session.commit()
    err = _error(post(client, headers, dropoff=IN_EXCLUDED))
    assert err["code"] == "OUT_OF_SERVICE_AREA"
    assert err["details"]["dropoff"]["reason"] == "UNSERVICEABLE_COMPONENT"
    assert fake_distance.reach.calls == 0 and fake_distance.calls == 0  # type: ignore[attr-defined]
    assert post(client, headers, dropoff=OUTSIDE_URBAN).status_code == 201  # outside the EXCLUDED part


def test_version_without_serviceability_layer_is_refused(client: TestClient, fake_distance: FakeDistance,
                                                        db_session: Session) -> None:
    _, headers = new_user(client)
    db_session.execute(text("UPDATE service_areas SET source_json = source_json - 'serviceability' "
                            "WHERE service_area_version = :v"), {"v": VERSION})
    db_session.commit()
    resp = post(client, headers)
    assert resp.status_code == 503 and resp.json()["error"]["code"] == "SERVICE_AREA_NOT_CONFIGURED"
