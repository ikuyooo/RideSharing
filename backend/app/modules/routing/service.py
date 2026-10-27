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

    def reachability(self, anchor: Lonlat, pickup: Lonlat, dropoff: Lonlat,
                     exclude: tuple[str, ...] = ()) -> Reachability:
        """One /table request over coordinates [anchor, pickup, dropoff] with
        sources [anchor, pickup] and destinations [pickup, dropoff]; the matrix is
          distances[0][0] = anchor -> pickup    distances[0][1] = anchor -> dropoff
          distances[1][0] = pickup -> pickup    distances[1][1] = pickup -> dropoff
        i.e. three DIRECT road distances (never the chained anchor -> pickup -> dropoff),
        in metres -> km, plus the snap distance of both points. `exclude` lists OSRM
        excludable classes (GEO-E: "ferry")."""
        params = {"sources": "0;1", "destinations": "1;2", "annotations": "distance"}
        if exclude:
            params["exclude"] = ",".join(exclude)
        body = self._get("table", [anchor, pickup, dropoff], params)
        dist = body["distances"]
        km = [[None if d is None else d / 1000.0 for d in row] for row in dist]
        snaps = [w["distance"] for w in body["destinations"]]
        return Reachability(
            pickup=PointReach(snap_m=snaps[0], anchor_road_km=km[0][0]),
            dropoff=PointReach(snap_m=snaps[1], anchor_road_km=km[0][1]),
            pickup_to_dropoff_km=km[1][1],
        )

    def road_distance(self, pickup: Lonlat, dropoff: Lonlat, exclude: tuple[str, ...] = ()) -> RoadDistance:
        """pickup/dropoff are (lon, lat). Distance is metres from OSRM, never duration."""
        params = {"overview": "false", "alternatives": "false", "steps": "false"}
        if exclude:
            params["exclude"] = ",".join(exclude)
        body = self._get("route", [pickup, dropoff], params)
        route = body["routes"][0]
        return RoadDistance(
            km=route["distance"] / 1000.0,
            pickup_snap_m=body["waypoints"][0]["distance"],
            dropoff_snap_m=body["waypoints"][1]["distance"],
        )
