"""OSRM implementation of the RoutingProvider (Revision 9 Section 34, P2-04).

`matrix()` is ONE `/table` request: the distinct coordinates of sources and
destinations are sent once, `sources` / `destinations` index into them, and
`annotations=distance,duration` returns both matrices. A request with more
distinct coordinates than the server's --max-table-size is refused here with
MatrixTooLarge - points are never dropped silently.

A fresh connection per request: osrm-routed v5.27.1 answers small keep-alive
requests ~40 ms late (Phase 0 finding).
"""

import time

import httpx

from app.modules.routing.provider import (
    Lonlat,
    Matrix,
    MatrixTooLarge,
    Profile,
    Route,
    RouteNotFound,
    RoutingPolicy,
    RoutingTimeout,
    RoutingUnavailable,
)


def osrm_get(base_url: str, timeout_s: float, service: str, coords: list[Lonlat], params: dict[str, str]) -> dict:
    path = ";".join(f"{lon:.6f},{lat:.6f}" for lon, lat in coords)
    try:
        resp = httpx.get(
            f"{base_url.rstrip('/')}/{service}/v1/driving/{path}",
            params=params,
            headers={"Connection": "close"},
            timeout=timeout_s,
        )
        body = resp.json()
    except httpx.TimeoutException as exc:
        raise RoutingTimeout(f"OSRM did not answer within {timeout_s} s") from exc
    except (httpx.HTTPError, ValueError) as exc:
        raise RoutingUnavailable(f"OSRM request failed: {type(exc).__name__}") from exc
    code = body.get("code") if isinstance(body, dict) else None
    if code in ("NoRoute", "NoSegment"):
        raise RouteNotFound(code)
    if resp.status_code != 200 or code != "Ok":
        raise RoutingUnavailable(f"OSRM answered HTTP {resp.status_code} code={code}")
    return body


class OsrmRoutingProvider:
    def __init__(self, base_urls: dict[Profile, str], timeout_s: float, policy: RoutingPolicy,
                 max_table_size: int) -> None:
        self._urls = base_urls
        self._timeout_s = timeout_s
        self._policy = policy
        self._max_table_size = max_table_size
        self.requests = 0  # instrumentation: OSRM HTTP requests made by this instance

    @property
    def policy(self) -> RoutingPolicy:
        return self._policy

    def _params(self, params: dict[str, str]) -> dict[str, str]:
        if self._policy.exclude:
            params["exclude"] = ",".join(self._policy.exclude)
        return params

    def _get(self, profile: Profile, service: str, coords: list[Lonlat], params: dict[str, str]) -> dict:
        self.requests += 1
        return osrm_get(self._urls[profile], self._timeout_s, service, coords, self._params(params))

    def route(self, profile: Profile, origin: Lonlat, destination: Lonlat,
              waypoints: tuple[Lonlat, ...] = ()) -> Route:
        coords = [origin, *waypoints, destination]
        body = self._get(profile, "route", coords,
                         {"overview": "false", "alternatives": "false", "steps": "false"})
        r = body["routes"][0]
        return Route(distance_m=float(r["distance"]), duration_s=float(r["duration"]),
                     snap_m=tuple(float(w["distance"]) for w in body["waypoints"]))

    def matrix(self, profile: Profile, sources: list[Lonlat], destinations: list[Lonlat]) -> Matrix:
        if not sources or not destinations:
            raise ValueError("a matrix needs at least one source and one destination")
        index: dict[Lonlat, int] = {}
        for p in (*sources, *destinations):
            index.setdefault(p, len(index))
        if len(index) > self._max_table_size:
            raise MatrixTooLarge(f"{len(index)} distinct coordinates > max table size {self._max_table_size}")
        coords = list(index)
        params = {"annotations": "distance,duration"}
        src = [index[p] for p in sources]
        dst = [index[p] for p in destinations]
        if src != list(range(len(coords))) or dst != list(range(len(coords))):
            params |= {"sources": ";".join(map(str, src)), "destinations": ";".join(map(str, dst))}
        started = time.perf_counter()
        body = self._get(profile, "table", coords, params)
        elapsed_ms = (time.perf_counter() - started) * 1000

        def cells(name: str) -> tuple[tuple[float | None, ...], ...]:
            rows = body.get(name)
            if rows is None or len(rows) != len(src) or any(len(row) != len(dst) for row in rows):
                raise RoutingUnavailable(f"OSRM table answer without a complete '{name}' matrix")
            return tuple(tuple(None if v is None else float(v) for v in row) for row in rows)

        return Matrix(distance_m=cells("distances"), duration_s=cells("durations"),
                      source_snap_m=tuple(float(w["distance"]) for w in body["sources"]),
                      destination_snap_m=tuple(float(w["distance"]) for w in body["destinations"]),
                      stats={"osrm_ms": elapsed_ms, "coordinates": len(coords),
                             "sources": len(src), "destinations": len(dst)})
