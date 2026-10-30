"""P2.2 / P2.3 - candidate generation on the throwaway database with the REAL OSRM
services: PostGIS filtering, one table per profile, the 11 hard constraints, branch A
insertion into a running vehicle's plan, run logging and explicit routing errors.
Drivers, trips and plans are SYNTHETIC (tests/p2_fixtures.py)."""

import socket
from datetime import UTC, datetime, timedelta

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import text
from sqlalchemy.orm import Session

from app.modules.routing.osrm import OsrmRoutingProvider
from app.modules.routing.provider import Profile, RoutingPolicy, RoutingUnavailable
from tests import p2_fixtures as fx
from tests.api_helpers import client, new_admin, new_user  # noqa: F401
from tests.conftest import _dotenv

pytestmark = [pytest.mark.db, pytest.mark.osrm]

PHENIKAA, HOAN_KIEM = (105.7477, 20.9426), (105.8520, 21.0285)
NOW = datetime.now(UTC).replace(microsecond=0)


def _urls() -> dict[Profile, str]:
    env = _dotenv()
    return {Profile.CAR: f"http://127.0.0.1:{env.get('OSRM_CAR_HOST_PORT', '5000')}",
            Profile.MOTORBIKE: f"http://127.0.0.1:{env.get('OSRM_MOTORBIKE_HOST_PORT', '5001')}"}


@pytest.fixture()
def provider() -> OsrmRoutingProvider:
    for url in _urls().values():
        host, port = url.removeprefix("http://").split(":")
        try:
            socket.create_connection((host, int(port)), timeout=1).close()
        except OSError:
            pytest.skip("OSRM not reachable")
    return OsrmRoutingProvider(_urls(), 5, RoutingPolicy(exclude=("ferry",), routing_version="test"), 200)


@pytest.fixture()
def world(app_env: None, db_session: Session, monkeypatch: pytest.MonkeyPatch) -> Session:
    from app.core.settings import get_settings

    monkeypatch.setenv("SERVICE_AREA_VERSION", fx.VERSION)
    get_settings.cache_clear()
    fx.setup_reference_data(db_session)
    return db_session


def _run(session: Session, provider: OsrmRoutingProvider, trip_id):  # type: ignore[no-untyped-def]
    from app.core.settings import get_settings
    from app.modules.candidate import service

    return service.run(session, get_settings(), trip_id, provider=provider, now=NOW)


def test_single_vehicle_candidates_follow_postgis_and_hard_constraints(world: Session,
                                                                       provider: OsrmRoutingProvider) -> None:
    s = world
    near = [(105.7500, 20.9450), (105.7450, 20.9400), (105.7550, 20.9480)]
    bikes = [fx.driver(s, lon, lat, NOW, vehicle_type="BIKE")[0] for lon, lat in near]
    fx.driver(s, 105.7480, 20.9430, NOW, vehicle_type="BIKE", availability="OFFLINE")   # HC01 / filter
    fx.driver(s, 105.7490, 20.9440, NOW, vehicle_type="BIKE", age_s=600)                # stale location
    fx.driver(s, 105.8300, 20.9900, NOW, vehicle_type="BIKE")                           # ~10 km: outside R_urban
    cars = [fx.driver(s, lon + 0.001, lat, NOW)[0] for lon, lat in near[:2]]
    pool_car = fx.driver(s, 105.7520, 20.9460, NOW, pool=True)[0]
    rider = fx.user(s)
    trip = fx.trip(s, rider, PHENIKAA, HOAN_KIEM, NOW)
    s.commit()

    stored, result = _run(s, provider, trip)
    assert result.status == "OK" and result.osrm_requests == 2 == provider.requests  # one table per profile
    assert result.counts["bike_drivers"] == 3 and result.counts["car_drivers"] == 3
    by = {}
    for c in result.candidates:
        by.setdefault(c.service_code, set()).add(c.driver_id)
    assert by["BIKE_URBAN"] == set(bikes)
    assert by["CAR_URBAN_PRIVATE"] == set(cars) | {pool_car}
    assert by["CAR_URBAN_POOL"] == {pool_car}  # branch B: pool-enabled, KYC VERIFIED only
    # Fares straight from the R9 formulas with OSRM route() of the right profile (independent of the table).
    bike_route = provider.route(Profile.MOTORBIKE, PHENIKAA, HOAN_KIEM)
    car_route = provider.route(Profile.CAR, PHENIKAA, HOAN_KIEM)
    bike_fare = int((10000 + 4500 * bike_route.distance_m / 1000 + 250 * bike_route.duration_s / 60) // 1000) * 1000
    private = int((20000 + 11000 * car_route.distance_m / 1000 + 500 * car_route.duration_s / 60) // 1000) * 1000
    quote = int(private * 0.8 // 1000) * 1000
    unmatched = int((quote + 0.5 * (private - quote)) // 1000) * 1000
    for c in result.candidates:
        window = c.audit["riders"][0]["window"]
        pickup = datetime.fromisoformat(c.insertion["planned_pickup"])
        assert datetime.fromisoformat(window[0]) <= pickup <= datetime.fromisoformat(window[1])
        assert datetime.fromisoformat(window[0]) == NOW + timedelta(minutes=3 if c.service_code == "BIKE_URBAN" else 5)
        if c.service_code == "BIKE_URBAN":
            assert c.expected_price_vnd == bike_fare
        elif c.service_code == "CAR_URBAN_PRIVATE":
            assert c.expected_price_vnd == private
        else:
            assert (c.pool_quote_vnd, c.pool_unmatched_vnd) == (quote, unmatched) and c.pricing_check == "COMPLETE"
    rows = s.execute(text("SELECT count(*) FROM ride_candidates WHERE run_id = :r"), {"r": stored.id}).scalar_one()
    assert rows == len(result.candidates)
    assert stored.timings_json["total"] > 0 and stored.routing_policy_json["exclude"] == ["ferry"]


def test_budget_cap_and_service_filter(world: Session, provider: OsrmRoutingProvider) -> None:
    s = world
    fx.driver(s, 105.7500, 20.9450, NOW, vehicle_type="BIKE")
    fx.driver(s, 105.7510, 20.9450, NOW, pool=True)
    rider = fx.user(s)
    trip = fx.trip(s, rider, PHENIKAA, HOAN_KIEM, NOW, budget_max=100000)  # bike fits, private / pool cap do not
    s.commit()
    _, result = _run(s, provider, trip)
    assert {c.service_code for c in result.candidates} == {"BIKE_URBAN"}
    assert result.rejections["CAR_URBAN_PRIVATE"]["HC08"] == 1 and result.rejections["CAR_URBAN_POOL"]["HC08"] == 1


def test_branch_a_inserts_into_a_running_vehicle(world: Session, provider: OsrmRoutingProvider) -> None:
    s = world
    # Rider A boarded at Phenikaa 10 minutes ago, going to Hoàn Kiếm; the car is now near Ngã Tư Sở.
    car, vehicle = fx.driver(s, 105.8195, 21.0035, NOW, pool=True, max_additional_pickups=2)
    a_user = fx.user(s)
    a_trip = fx.trip(s, a_user, PHENIKAA, HOAN_KIEM, NOW - timedelta(minutes=20), allowed=["CAR_URBAN_POOL"])
    direct = provider.route(Profile.CAR, PHENIKAA, HOAN_KIEM)
    plan = fx.onboard_plan(s, car, vehicle, a_trip, a_user, PHENIKAA, HOAN_KIEM, NOW - timedelta(minutes=10),
                           direct_m=direct.distance_m, direct_s=direct.duration_s,
                           traveled_km=provider.route(Profile.CAR, PHENIKAA, (105.8195, 21.0035)).distance_m / 1000,
                           cap_vnd=174000)
    b_user = fx.user(s)
    b_trip = fx.trip(s, b_user, (105.8230, 21.0060), (105.8470, 21.0250), NOW, allowed=["CAR_URBAN_POOL"])
    s.commit()
    stored, result = _run(s, provider, b_trip)
    assert result.counts["pool_plans"] == 1 and result.osrm_requests == 1
    a = [c for c in result.candidates if c.source_type == "EXISTING_POOL_PLAN"]
    assert len(a) == 1 and a[0].plan_id == plan and a[0].plan_version == 3
    assert a[0].pricing_check == "PENDING_P3"  # steps 4-5 of Section 36 belong to Phase 3
    riders = {r["ref"]: r for r in a[0].audit["riders"]}
    assert len(riders) == 2 and any(r["onboard"] for r in riders.values())  # rider A was re-checked
    for r in riders.values():
        assert r["detour"] <= r["max_detour"] and r["in_vehicle_s"] <= r["max_in_vehicle_s"]
    onboard_ref = next(k for k, r in riders.items() if r["onboard"])
    chain = a[0].insertion["chain"]
    assert ["new", "PICKUP"] in chain and ["new", "DROPOFF"] in chain and [onboard_ref, "DROPOFF"] in chain
    assert chain.index(["new", "PICKUP"]) < chain.index(["new", "DROPOFF"])


def test_routing_unavailable_is_explicit_and_logged(world: Session) -> None:
    s = world
    fx.driver(s, 105.7500, 20.9450, NOW, vehicle_type="BIKE")
    trip = fx.trip(s, fx.user(s), PHENIKAA, HOAN_KIEM, NOW)
    s.commit()

    class Down:
        def matrix(self, *args: object) -> None:
            raise RoutingUnavailable("down")

    from app.core.errors import ApiError

    with pytest.raises(ApiError) as err:
        _run(s, Down(), trip)  # type: ignore[arg-type]
    assert err.value.status_code == 503 and err.value.code == "ROUTING_UNAVAILABLE"
    status = s.execute(text("SELECT status FROM candidate_runs WHERE request_id = :t"), {"t": trip}).scalar_one()
    assert status == "ROUTING_UNAVAILABLE"
    assert s.execute(text("SELECT count(*) FROM ride_candidates WHERE request_id = :t"), {"t": trip}).scalar_one() == 0


def test_admin_api_and_driver_availability(world: Session, client: TestClient,  # noqa: F811
                                           provider: OsrmRoutingProvider, monkeypatch: pytest.MonkeyPatch) -> None:
    from app.core.settings import get_settings

    monkeypatch.setenv("OSRM_CAR_URL", _urls()[Profile.CAR])
    monkeypatch.setenv("OSRM_MOTORBIKE_URL", _urls()[Profile.MOTORBIKE])
    get_settings.cache_clear()
    _, admin = new_admin(client, world)
    _, passenger = new_user(client)
    assert client.post("/api/admin/candidates/runs", json={"request_id": str(fx.user(world))},
                       headers=passenger).status_code == 403
    # driver goes online through the API (technical addition), then is found
    _, drv = new_user(client, role="DRIVER")
    assert client.put("/api/driver/availability", json={"availability": "IDLE"}, headers=drv).status_code == 409
    assert client.put("/api/driver/location", json={"lat": 20.9450, "lon": 105.7500}, headers=drv).status_code == 204
    vehicle = client.post("/api/driver/vehicles", json={"vehicle_type": "BIKE", "license_plate": "29-B1 123.45"},
                          headers=drv).json()
    resp = client.put("/api/driver/availability", json={"availability": "IDLE", "vehicle_id": vehicle["id"]}, headers=drv)
    assert resp.status_code == 204
    profile = client.get("/api/driver/profile", headers=drv).json()
    client.put("/api/driver/settings", json={"accepts_urban": True}, headers=drv)
    trip = fx.trip(world, fx.user(world), PHENIKAA, HOAN_KIEM, datetime.now(UTC), allowed=["BIKE_URBAN"])
    world.commit()
    out = client.post("/api/admin/candidates/runs", json={"request_id": str(trip)}, headers=admin)
    assert out.status_code == 201, out.text
    body = out.json()
    assert body["status"] == "OK" and [c["driver_id"] for c in body["candidates"]] == [profile["user_id"]]
    again = client.get(f"/api/admin/candidates/runs/{body['run_id']}", headers=admin).json()
    assert again["candidates"][0]["constraint_audit"]["checked"] == "HC01-HC11"
