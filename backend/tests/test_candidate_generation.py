"""P2.2 / P2.3 - candidate generation on the throwaway database with the REAL OSRM
services: PostGIS filtering, one table per profile, the 11 hard constraints, branch A
insertion into a running vehicle's plan, run logging and explicit routing errors.
Drivers, trips and plans are SYNTHETIC (tests/p2_fixtures.py)."""

import socket
from datetime import UTC, datetime, timedelta
from fractions import Fraction

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
    # One car table: origins = vehicle (S_curr), stop ahead, P, Q; destinations = stop ahead, P, Q only.
    assert result.counts["car_matrix"][:2] == [4, 3]
    # Every option was evaluated by the 11 hard constraints and then by the Phase 3 pricing. On real
    # OSRM (free-flow speeds, no traffic) this plan fails gate 2B: the co-rider's single-ride hourly rate
    # beats the plan's (SF-P3-16) - an exact reason code, no candidate, nothing priced from guesses.
    assert not [c for c in result.candidates if c.source_type == "EXISTING_POOL_PLAN"]
    rej = result.rejections["CAR_URBAN_POOL"]
    assert set(rej) <= {"HC03", "HC05", "P3_D1_NO_CO_RIDING_OVERLAP", "P3_GATE1_PASSENGER_SHAREABILITY",
                        "P3_GATE2B_DRIVER_HOURLY_RATE"}, rej
    assert any(code.startswith("P3_") for code in rej), rej        # pricing ran on HC-feasible options


class TrafficSpeedRouter:
    """Deterministic SYNTHETIC router: road distance = 1,3 x great-circle distance, 20 km/h (urban
    traffic, like the 21 km/h of the Section 16.1 example). Only for the pricing path of branch A."""

    def __init__(self) -> None:
        self.calls = 0

    @staticmethod
    def _leg(a, b):  # type: ignore[no-untyped-def]
        import math
        lat = math.radians((a[1] + b[1]) / 2)
        dx = (b[0] - a[0]) * 111320 * math.cos(lat)
        dy = (b[1] - a[1]) * 110540
        d = 1.3 * math.hypot(dx, dy)
        return d, d / (20 / 3.6)

    def route(self, profile, origin, destination, **_):  # type: ignore[no-untyped-def]
        from app.modules.routing.provider import Route
        d, t = self._leg(origin, destination)
        return Route(d, t, (0.0, 0.0))

    def matrix(self, profile, sources, destinations):  # type: ignore[no-untyped-def]
        from app.modules.routing.provider import Matrix
        self.calls += 1
        legs = [[self._leg(a, b) for b in destinations] for a in sources]
        return Matrix(tuple(tuple(x[0] for x in row) for row in legs), tuple(tuple(x[1] for x in row) for row in legs),
                      tuple(0.0 for _ in sources), tuple(0.0 for _ in destinations), {"sources": len(sources),
                                                                                       "destinations": len(destinations)})


def test_branch_a_with_traffic_speeds_is_priced_complete(world: Session) -> None:
    """Branch A end to end through PoolPricingCheck (Phase 3): gate 1, D1-D6, allocation, rounding, gate 2."""
    s = world
    router = TrafficSpeedRouter()
    car_pos = (105.7700, 20.9600)
    car, vehicle = fx.driver(s, *car_pos, NOW, pool=True, max_additional_pickups=2)
    a_user = fx.user(s)
    a_trip = fx.trip(s, a_user, PHENIKAA, HOAN_KIEM, NOW - timedelta(minutes=40), allowed=["CAR_URBAN_POOL"])
    direct = router.route(Profile.CAR, PHENIKAA, HOAN_KIEM)
    driven = router.route(Profile.CAR, PHENIKAA, car_pos)
    plan = fx.onboard_plan(s, car, vehicle, a_trip, a_user, PHENIKAA, HOAN_KIEM,
                           NOW - timedelta(seconds=driven.duration_s + 60), direct_m=direct.distance_m,
                           direct_s=direct.duration_s, traveled_km=driven.distance_m / 1000, cap_vnd=400000)
    b_user = fx.user(s)
    # B booked 5 min ago (its NOW window is open: no wait) and shares most of A's remaining route
    b_trip = fx.trip(s, b_user, (105.7720, 20.9620), HOAN_KIEM, NOW - timedelta(minutes=5), allowed=["CAR_URBAN_POOL"])
    s.commit()
    _, result = _run(s, router, b_trip)  # type: ignore[arg-type]
    a = [c for c in result.candidates if c.source_type == "EXISTING_POOL_PLAN"]
    assert len(a) == 1, result.rejections["CAR_URBAN_POOL"]
    c = a[0]
    assert c.plan_id == plan and c.pricing_check == "COMPLETE"
    riders = {r["ref"]: r for r in c.audit["riders"]}
    assert len(riders) == 2 and any(r["onboard"] for r in riders.values())  # rider A was re-checked
    for r in riders.values():
        assert r["detour"] <= r["max_detour"] and r["in_vehicle_s"] <= r["max_in_vehicle_s"]
    chain = c.insertion["chain"]
    assert chain.index(["new", "PICKUP"]) < chain.index(["new", "DROPOFF"])
    from app.modules.candidate.service import offerable
    assert offerable(c.pricing_check)
    pricing = c.insertion["pricing"]
    exact = {ref: Fraction(x["fare_exact"]) for ref, x in pricing["riders"].items()}
    assert sum(exact.values()) == Fraction(pricing["plan_fare"])            # N1, exactly
    assert c.fare_matched_est_vnd == pricing["riders"]["new"]["fare_charged"] <= c.pool_quote_vnd
    old_ref = next(r for r in pricing["riders"] if r != "new")
    assert pricing["riders"][old_ref]["group"] == "U"                        # first match: allocated on Cap
    charged = sum(x["fare_charged"] for x in pricing["riders"].values())
    assert Fraction(pricing["driver_payout"]) == Fraction(85, 100) * charged
    stored = s.execute(text("SELECT pricing_check, fare_matched_est_vnd FROM ride_candidates "
                            "WHERE target_plan_id = :p"), {"p": plan}).one()
    assert tuple(stored) == ("COMPLETE", c.fare_matched_est_vnd)


def test_branch_a_plan_without_pricing_state_is_never_priced_from_guesses(world: Session,
                                                                         provider: OsrmRoutingProvider) -> None:
    s = world
    car, vehicle = fx.driver(s, 105.8195, 21.0035, NOW, pool=True, max_additional_pickups=2)
    a_user = fx.user(s)
    a_trip = fx.trip(s, a_user, PHENIKAA, HOAN_KIEM, NOW - timedelta(minutes=20), allowed=["CAR_URBAN_POOL"])
    direct = provider.route(Profile.CAR, PHENIKAA, HOAN_KIEM)
    plan = fx.onboard_plan(s, car, vehicle, a_trip, a_user, PHENIKAA, HOAN_KIEM, NOW - timedelta(minutes=10),
                           direct_m=direct.distance_m, direct_s=direct.duration_s, traveled_km=7.0, cap_vnd=174000)
    s.execute(text("UPDATE ride_plans SET pricing_version = NULL WHERE id = :p"), {"p": plan})
    b_user = fx.user(s)
    b_trip = fx.trip(s, b_user, (105.8230, 21.0060), (105.8470, 21.0250), NOW, allowed=["CAR_URBAN_POOL"])
    s.commit()
    _, result = _run(s, provider, b_trip)
    assert not [c for c in result.candidates if c.source_type == "EXISTING_POOL_PLAN"]
    assert result.rejections["CAR_URBAN_POOL"]["P3_PLAN_PRICING_STATE"] >= 1


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


def test_one_spatial_query_returns_the_same_lists_as_one_query_per_list(world: Session) -> None:
    """PostGIS optimisation P1: the merged query (one scan, row_number per list) returns exactly
    the lists of three separate `WHERE ... ORDER BY distance LIMIT 15` queries (old behaviour)."""
    import random

    from app.modules.driver.service import nearby_idle_drivers

    s, rng = world, random.Random(7)
    for i in range(300):
        lon, lat = 105.80 + rng.uniform(-0.06, 0.06), 21.02 + rng.uniform(-0.05, 0.05)
        kind = i % 4
        fx.driver(s, lon, lat, NOW, vehicle_type="BIKE" if kind == 0 else "CAR4", pool=kind == 1,
                  availability="OFFLINE" if i % 17 == 0 else "IDLE", age_s=600 if i % 23 == 0 else 5,
                  accepts_urban=i % 29 != 0)
    s.commit()
    p = (105.80, 21.02)
    got = nearby_idle_drivers(s, p[0], p[1], 5000, 15, NOW, 120)

    def old(where: str) -> list:
        return list(s.execute(text(
            "SELECT dl.driver_id FROM driver_locations dl JOIN driver_profiles dp ON dp.user_id = dl.driver_id "
            "JOIN vehicles v ON v.id = dl.active_vehicle_id WHERE dl.availability = 'IDLE' "
            "AND dl.updated_at >= :now - interval '120 seconds' AND v.is_active AND dp.accepts_urban AND " + where +
            " AND ST_DWithin(dl.geom::geography, ST_SetSRID(ST_MakePoint(:x, :y), 4326)::geography, 5000) "
            "ORDER BY ST_Distance(dl.geom::geography, ST_SetSRID(ST_MakePoint(:x, :y), 4326)::geography) LIMIT 15"),
            {"now": NOW, "x": p[0], "y": p[1]}).scalars())

    assert [d.driver_id for d in got["BIKE"]] == old("v.vehicle_type = 'BIKE'")
    assert [d.driver_id for d in got["CAR4"]] == old("v.vehicle_type = 'CAR4'")
    assert [d.driver_id for d in got["CAR4_POOL"]] == old(
        "v.vehicle_type = 'CAR4' AND dp.pool_enabled AND dp.kyc_status = 'VERIFIED'")
    assert all(len(v) == 15 for v in got.values())  # enough drivers: every list is full
