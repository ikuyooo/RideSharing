"""routing service - Phase 1 minimal interface (owner decision P1-D2).

Only what Trip Intent classification needs: the shortest road distance of the
OSRM car profile between two points, and the per-point reachability used by the
service-area serviceability layer (GEO-03). The full RoutingProvider (route/matrix,
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


@dataclass(frozen=True)
class PointReach:
    snap_m: float                  # distance from the point to the snapped road position
    anchor_road_km: float | None   # car road distance from the anchor; None = no route


@dataclass(frozen=True)
class Reachability:
    pickup: PointReach
    dropoff: PointReach
    pickup_to_dropoff_km: float | None  # None = no route between the two points


Lonlat = tuple[float, float]


class OsrmCarDistance:
    def __init__(self, base_url: str, timeout_s: float) -> None:
        self._base_url = base_url.rstrip("/")
        self._timeout_s = timeout_s

    def _get(self, service: str, coords: list[Lonlat], params: dict[str, str]) -> dict:
        path = ";".join(f"{lon:.6f},{lat:.6f}" for lon, lat in coords)
        try:
            # A fresh connection per request: osrm-routed v5.27.1 answers small
            # keep-alive requests ~40 ms late (Phase 0 finding).
            resp = httpx.get(
                f"{self._base_url}/{service}/v1/driving/{path}",
                params=params,
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
        return body

    def reachability(self, anchor: Lonlat, pickup: Lonlat, dropoff: Lonlat) -> Reachability:
        """One /table request: anchor->pickup, anchor->dropoff, pickup->dropoff road
        distances (metres -> km) and the snap distance of both points."""
        body = self._get("table", [anchor, pickup, dropoff],
                         {"sources": "0;1", "destinations": "1;2", "annotations": "distance"})
        dist = body["distances"]
        km = [[None if d is None else d / 1000.0 for d in row] for row in dist]
        snaps = [w["distance"] for w in body["destinations"]]
        return Reachability(
            pickup=PointReach(snap_m=snaps[0], anchor_road_km=km[0][0]),
            dropoff=PointReach(snap_m=snaps[1], anchor_road_km=km[0][1]),
            pickup_to_dropoff_km=km[1][1],
        )

    def road_distance(self, pickup: Lonlat, dropoff: Lonlat) -> RoadDistance:
        """pickup/dropoff are (lon, lat). Distance is metres from OSRM, never duration."""
        body = self._get("route", [pickup, dropoff],
                         {"overview": "false", "alternatives": "false", "steps": "false"})
        route = body["routes"][0]
        return RoadDistance(
            km=route["distance"] / 1000.0,
            pickup_snap_m=body["waypoints"][0]["distance"],
            dropoff_snap_m=body["waypoints"][1]["distance"],
        )
