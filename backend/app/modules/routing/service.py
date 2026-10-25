"""routing service - Phase 1 minimal interface (owner decision P1-D2).

Only what Trip Intent classification needs: the shortest road distance of the
OSRM car profile between two points. The full RoutingProvider (route/matrix,
Redis cache, motorbike) is Phase 2 (Revision 9 Sections 34, 79).

Errors are explicit; there is NO fallback to a straight-line distance.
"""

from dataclasses import dataclass

import httpx


class RouteNotFound(Exception):
    """OSRM answered but has no route (NoRoute / NoSegment)."""


class RoutingUnavailable(Exception):
    """OSRM could not be reached or answered with an unexpected error."""


@dataclass(frozen=True)
class RoadDistance:
    km: float
    pickup_snap_m: float
    dropoff_snap_m: float


class OsrmCarDistance:
    def __init__(self, base_url: str, timeout_s: float) -> None:
        self._base_url = base_url.rstrip("/")
        self._timeout_s = timeout_s

    def road_distance(self, pickup: tuple[float, float], dropoff: tuple[float, float]) -> RoadDistance:
        """pickup/dropoff are (lon, lat). Distance is metres from OSRM, never duration."""
        coords = f"{pickup[0]:.6f},{pickup[1]:.6f};{dropoff[0]:.6f},{dropoff[1]:.6f}"
        try:
            # A fresh connection per request: osrm-routed v5.27.1 answers small
            # keep-alive requests ~40 ms late (Phase 0 finding).
            resp = httpx.get(
                f"{self._base_url}/route/v1/driving/{coords}",
                params={"overview": "false", "alternatives": "false", "steps": "false"},
                headers={"Connection": "close"},
                timeout=self._timeout_s,
            )
            body = resp.json()
        except (httpx.HTTPError, ValueError) as exc:
            raise RoutingUnavailable(f"OSRM request failed: {type(exc).__name__}") from exc
        code = body.get("code")
        if code in ("NoRoute", "NoSegment"):
            raise RouteNotFound(code)
        if resp.status_code != 200 or code != "Ok":
            raise RoutingUnavailable(f"OSRM answered HTTP {resp.status_code} code={code}")
        route = body["routes"][0]
        return RoadDistance(
            km=route["distance"] / 1000.0,
            pickup_snap_m=body["waypoints"][0]["distance"],
            dropoff_snap_m=body["waypoints"][1]["distance"],
        )
