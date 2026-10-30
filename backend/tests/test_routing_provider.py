"""P2.1 - RoutingProvider (Revision 9 Section 34): one /table request per matrix, both
profiles, explicit errors without straight-line fallback, Redis cache per policy."""

import json
import socket

import httpx
import pytest
import redis

from app.modules.routing.cache import CachedRoutingProvider, cache_key, geohash
from app.modules.routing.osrm import OsrmRoutingProvider
from app.modules.routing.provider import (
    MatrixTooLarge,
    Profile,
    RouteNotFound,
    RoutingPolicy,
    RoutingTimeout,
    RoutingUnavailable,
)
from tests.conftest import _dotenv

POLICY = RoutingPolicy(exclude=("ferry",), routing_version="test-graph")
URLS = {Profile.CAR: "http://osrm-car", Profile.MOTORBIKE: "http://osrm-bike"}
HOAN_KIEM, PHENIKAA, HA_DONG = (105.8520, 21.0285), (105.7477, 20.9426), (105.7760, 20.9710)


def _provider(max_table: int = 200) -> OsrmRoutingProvider:
    return OsrmRoutingProvider(URLS, 1, POLICY, max_table)


def _fake(monkeypatch: pytest.MonkeyPatch, status: int, body: object, seen: list | None = None) -> None:
    def fake_get(url: str, params: dict, **kwargs: object) -> httpx.Response:
        if seen is not None:
            seen.append((url, params))
        return httpx.Response(status, content=json.dumps(body).encode())

    monkeypatch.setattr(httpx, "get", fake_get)


def test_matrix_is_one_table_request_with_distinct_coordinates(monkeypatch: pytest.MonkeyPatch) -> None:
    seen: list = []
    body = {"code": "Ok", "distances": [[0.0, 1000.0], [900.0, None]], "durations": [[0.0, 100.0], [95.0, None]],
            "sources": [{"distance": 1.5}, {"distance": 2.0}], "destinations": [{"distance": 2.0}, {"distance": 3.0}]}
    _fake(monkeypatch, 200, body, seen)
    p = _provider()
    m = p.matrix(Profile.MOTORBIKE, [HOAN_KIEM, PHENIKAA], [PHENIKAA, HA_DONG])
    assert len(seen) == 1 and p.requests == 1
    url, params = seen[0]
    # PHENIKAA appears in both lists but is sent once: 3 distinct coordinates.
    assert url.startswith("http://osrm-bike/table/v1/driving/105.852000,21.028500;105.747700,20.942600;105.776000,20.971000")
    assert params == {"annotations": "distance,duration", "sources": "0;1", "destinations": "1;2", "exclude": "ferry"}
    assert m.distance_m[0][1] == 1000.0 and m.duration_s[1][0] == 95.0
    assert m.routable(0, 0) and not m.routable(1, 1)  # a null cell means no road, not an error
    assert m.source_snap_m == (1.5, 2.0) and m.stats["coordinates"] == 3


def test_square_matrix_sends_no_index_lists(monkeypatch: pytest.MonkeyPatch) -> None:
    seen: list = []
    body = {"code": "Ok", "distances": [[0.0, 5.0], [5.0, 0.0]], "durations": [[0.0, 1.0], [1.0, 0.0]],
            "sources": [{"distance": 0}, {"distance": 0}], "destinations": [{"distance": 0}, {"distance": 0}]}
    _fake(monkeypatch, 200, body, seen)
    pts = [HOAN_KIEM, PHENIKAA]
    _provider().matrix(Profile.CAR, pts, pts)
    assert seen[0][0].startswith("http://osrm-car/table/") and seen[0][1] == {"annotations": "distance,duration",
                                                                              "exclude": "ferry"}


def test_matrix_larger_than_server_limit_is_refused_not_truncated(monkeypatch: pytest.MonkeyPatch) -> None:
    seen: list = []
    _fake(monkeypatch, 200, {}, seen)
    pts = [(105.0 + i / 1000, 21.0) for i in range(4)]
    with pytest.raises(MatrixTooLarge):
        _provider(max_table=3).matrix(Profile.CAR, pts, pts)
    assert seen == []


def test_incomplete_table_answer_is_unavailable(monkeypatch: pytest.MonkeyPatch) -> None:
    _fake(monkeypatch, 200, {"code": "Ok", "distances": [[1.0]], "sources": [{"distance": 0}],
                             "destinations": [{"distance": 0}]})
    with pytest.raises(RoutingUnavailable):
        _provider().matrix(Profile.CAR, [HOAN_KIEM], [PHENIKAA])


@pytest.mark.parametrize(("status", "body", "error"), [
    (400, {"code": "NoRoute"}, RouteNotFound),
    (400, {"code": "NoSegment"}, RouteNotFound),
    (400, {"code": "InvalidOptions"}, RoutingUnavailable),
    (502, {"message": "bad gateway"}, RoutingUnavailable),
    (200, ["not", "an", "object"], RoutingUnavailable),
])
def test_osrm_errors_are_explicit(monkeypatch: pytest.MonkeyPatch, status: int, body: object, error: type) -> None:
    _fake(monkeypatch, status, body)
    with pytest.raises(error):
        _provider().route(Profile.CAR, HOAN_KIEM, PHENIKAA)


def test_timeout_and_network_errors(monkeypatch: pytest.MonkeyPatch) -> None:
    def timeout(*args: object, **kwargs: object) -> httpx.Response:
        raise httpx.ReadTimeout("slow")

    monkeypatch.setattr(httpx, "get", timeout)
    with pytest.raises(RoutingTimeout):
        _provider().matrix(Profile.CAR, [HOAN_KIEM], [PHENIKAA])
    monkeypatch.undo()
    with pytest.raises(RoutingUnavailable):
        OsrmRoutingProvider({Profile.CAR: "http://127.0.0.1:1"}, 1, POLICY, 200).route(Profile.CAR, HOAN_KIEM, PHENIKAA)


def test_geohash_matches_reference_values() -> None:
    assert geohash(-5.6, 42.6, 5) == "ezs42"            # Wikipedia reference
    assert geohash(105.8520, 21.0285) == geohash(105.85201, 21.02851)
    assert len(geohash(105.8520, 21.0285)) == 7


def test_cache_key_changes_with_policy_and_profile() -> None:
    k = cache_key(POLICY, Profile.CAR, HOAN_KIEM, PHENIKAA)
    assert k.endswith(":static") and ":car:" in k
    assert k != cache_key(POLICY, Profile.MOTORBIKE, HOAN_KIEM, PHENIKAA)
    assert k != cache_key(RoutingPolicy(exclude=(), routing_version="test-graph"), Profile.CAR, HOAN_KIEM, PHENIKAA)
    assert k != cache_key(RoutingPolicy(exclude=("ferry",), routing_version="other"), Profile.CAR, HOAN_KIEM, PHENIKAA)


class CountingInner:
    def __init__(self) -> None:
        self.routes = self.matrices = 0

    def route(self, profile, origin, destination, waypoints=()):  # type: ignore[no-untyped-def]
        from app.modules.routing.provider import Route

        self.routes += 1
        return Route(distance_m=1234.5, duration_s=98.7, snap_m=(1.0, 2.0))

    def matrix(self, profile, sources, destinations):  # type: ignore[no-untyped-def]
        self.matrices += 1
        return None


class BrokenRedis:
    def get(self, key: str) -> None:
        raise redis.ConnectionError("down")

    def set(self, *args: object, **kwargs: object) -> None:
        raise redis.ConnectionError("down")


def _redis_url() -> str:
    env = _dotenv()
    return f"redis://:{env.get('REDIS_PASSWORD', '')}@127.0.0.1:{env.get('REDIS_HOST_PORT', '6379')}/14"


def _redis_reachable() -> bool:
    env = _dotenv()
    try:
        with socket.create_connection(("127.0.0.1", int(env.get("REDIS_HOST_PORT", "6379"))), timeout=1):
            return True
    except OSError:
        return False


@pytest.mark.redis
def test_route_cache_hit_miss_on_real_redis() -> None:
    if not _redis_reachable():
        pytest.skip("Redis not reachable")
    client = redis.Redis.from_url(_redis_url())
    key = cache_key(POLICY, Profile.CAR, HOAN_KIEM, PHENIKAA)
    client.delete(key)
    inner = CountingInner()
    cached = CachedRoutingProvider(inner, POLICY, client, ttl_s=60)
    try:
        first, second = cached.route(Profile.CAR, HOAN_KIEM, PHENIKAA), cached.route(Profile.CAR, HOAN_KIEM, PHENIKAA)
        assert first == second and inner.routes == 1 and (cached.hits, cached.misses) == (1, 1)
        assert 0 < client.ttl(key) <= 60
        cached.route(Profile.MOTORBIKE, HOAN_KIEM, PHENIKAA)
        assert inner.routes == 2  # another profile is another key
        cached.matrix(Profile.CAR, [HOAN_KIEM], [PHENIKAA])
        cached.matrix(Profile.CAR, [HOAN_KIEM], [PHENIKAA])
        assert inner.matrices == 2  # matrices are never cached (OD-P2-02)
    finally:
        client.delete(key, cache_key(POLICY, Profile.MOTORBIKE, HOAN_KIEM, PHENIKAA))


def test_cache_failure_falls_through_to_osrm() -> None:
    inner = CountingInner()
    cached = CachedRoutingProvider(inner, POLICY, BrokenRedis(), ttl_s=60)  # type: ignore[arg-type]
    assert cached.route(Profile.CAR, HOAN_KIEM, PHENIKAA).distance_m == 1234.5
    assert inner.routes == 1


def _osrm_urls() -> dict[Profile, str]:
    env = _dotenv()
    return {Profile.CAR: f"http://127.0.0.1:{env.get('OSRM_CAR_HOST_PORT', '5000')}",
            Profile.MOTORBIKE: f"http://127.0.0.1:{env.get('OSRM_MOTORBIKE_HOST_PORT', '5001')}"}


def _osrm_reachable() -> bool:
    try:
        for url in _osrm_urls().values():
            host, port = url.removeprefix("http://").split(":")
            socket.create_connection((host, int(port)), timeout=1).close()
        return True
    except OSError:
        return False


@pytest.mark.osrm
@pytest.mark.parametrize("profile", list(Profile))
def test_real_matrix_matches_pairwise_routes(profile: Profile) -> None:
    if not _osrm_reachable():
        pytest.skip("OSRM not reachable")
    p = OsrmRoutingProvider(_osrm_urls(), 5, POLICY, 200)
    pts = [HOAN_KIEM, PHENIKAA, HA_DONG, (105.8010, 21.0050)]
    m = p.matrix(profile, pts, pts)
    assert p.requests == 1
    for i, a in enumerate(pts):
        for j, b in enumerate(pts):
            if i == j:
                continue
            r = p.route(profile, a, b)
            assert m.distance_m[i][j] == pytest.approx(r.distance_m, abs=1.0)
            assert m.duration_s[i][j] == pytest.approx(r.duration_s, abs=1.0)
