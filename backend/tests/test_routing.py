"""P1.5 - minimal OSRM car distance client (owner decision P1-D2)."""

import json
import socket

import httpx
import pytest

from app.modules.routing.service import OsrmCarDistance, RouteNotFound, RoutingUnavailable
from tests.conftest import _dotenv


def _osrm_car_url() -> str:
    return f"http://127.0.0.1:{_dotenv().get('OSRM_CAR_HOST_PORT', '5000')}"


def _reachable(url: str) -> bool:
    host, port = url.removeprefix("http://").split(":")
    try:
        with socket.create_connection((host, int(port)), timeout=1):
            return True
    except OSError:
        return False


@pytest.mark.osrm
def test_real_osrm_returns_road_distance_not_duration() -> None:
    url = _osrm_car_url()
    if not _reachable(url):
        pytest.skip(f"OSRM car not reachable at {url}")
    client = OsrmCarDistance(url, timeout_s=5)
    # Phenikaa -> Đống Đa (Phase 0 smoke-check pair); compare with OSRM's own route.
    result = client.road_distance((105.7477, 20.9426), (105.8270, 21.0180))
    raw = httpx.get(f"{url}/route/v1/driving/105.7477,20.9426;105.8270,21.0180?overview=false").json()
    assert result.km == pytest.approx(raw["routes"][0]["distance"] / 1000)
    assert result.km != pytest.approx(raw["routes"][0]["duration"] / 1000)
    assert result.pickup_snap_m >= 0 and result.dropoff_snap_m >= 0


def _fake_response(monkeypatch: pytest.MonkeyPatch, status: int, body: dict) -> None:
    def fake_get(*args: object, **kwargs: object) -> httpx.Response:
        return httpx.Response(status, content=json.dumps(body).encode())

    monkeypatch.setattr(httpx, "get", fake_get)


@pytest.mark.parametrize("code", ["NoRoute", "NoSegment"])
def test_no_route_is_explicit(monkeypatch: pytest.MonkeyPatch, code: str) -> None:
    _fake_response(monkeypatch, 400, {"code": code})
    with pytest.raises(RouteNotFound):
        OsrmCarDistance("http://osrm", 1).road_distance((105.0, 21.0), (105.1, 21.1))


def test_unexpected_answer_is_unavailable(monkeypatch: pytest.MonkeyPatch) -> None:
    _fake_response(monkeypatch, 400, {"code": "InvalidValue"})
    with pytest.raises(RoutingUnavailable):
        OsrmCarDistance("http://osrm", 1).road_distance((105.0, 21.0), (105.1, 21.1))


def test_unreachable_server_is_unavailable() -> None:
    with pytest.raises(RoutingUnavailable):
        OsrmCarDistance("http://127.0.0.1:1", 1).road_distance((105.0, 21.0), (105.1, 21.1))


def test_reachability_parses_one_table_request(monkeypatch: pytest.MonkeyPatch) -> None:
    """GEO-03 tier 2: anchor->pickup, anchor->dropoff, pickup->dropoff and snap distances."""
    seen: dict = {}

    def fake_get(url: str, params: dict, **kwargs: object) -> httpx.Response:
        seen["url"], seen["params"] = url, params
        body = {"code": "Ok", "distances": [[150000.0, None], [0.0, 12345.0]],
                "sources": [{"distance": 1.0}, {"distance": 2.5}],
                "destinations": [{"distance": 2.5}, {"distance": 301.0}]}
        return httpx.Response(200, content=json.dumps(body).encode())

    monkeypatch.setattr(httpx, "get", fake_get)
    r = OsrmCarDistance("http://osrm", 1).reachability((105.85, 21.03), (105.0, 21.0), (105.1, 21.1))
    assert "/table/v1/driving/105.850000,21.030000;105.000000,21.000000;105.100000,21.100000" in seen["url"]
    assert seen["params"] == {"sources": "0;1", "destinations": "1;2", "annotations": "distance"}
    assert r.pickup.anchor_road_km == 150.0 and r.pickup.snap_m == 2.5
    assert r.dropoff.anchor_road_km is None and r.dropoff.snap_m == 301.0
    assert r.pickup_to_dropoff_km == pytest.approx(12.345)


@pytest.mark.osrm
def test_real_osrm_reachability_matches_route() -> None:
    url = _osrm_car_url()
    if not _reachable(url):
        pytest.skip(f"OSRM car not reachable at {url}")
    client = OsrmCarDistance(url, timeout_s=5)
    anchor, a, b = (105.854041, 21.0283334), (105.7477, 20.9426), (105.8270, 21.0180)
    r = client.reachability(anchor, a, b)
    assert r.pickup_to_dropoff_km == pytest.approx(client.road_distance(a, b).km, rel=1e-3)
    assert r.pickup.anchor_road_km == pytest.approx(client.road_distance(anchor, a).km, rel=1e-3)
    assert 0 <= r.pickup.snap_m < 300 and 0 <= r.dropoff.snap_m < 300
