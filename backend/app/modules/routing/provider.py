"""RoutingProvider interface (Revision 9 Section 34).

    RoutingProvider.route(profile, origin, destination, waypoints=[])
    RoutingProvider.matrix(profile, sources, destinations)

Two profiles: `car` (motorways allowed) and `motorbike` (no motorway). Coordinates
are (lon, lat). Every request carries the routing policy of the service area
(GEO-E: `exclude=ferry`). Errors are explicit and there is NO straight-line
fallback: an unreachable engine raises RoutingUnavailable; a request OSRM cannot
route raises RouteNotFound; a matrix cell without a road is None (constraint 2
rejects that pair, the rest of the matrix stays usable).
"""

import hashlib
import json
from dataclasses import dataclass, field
from enum import StrEnum
from typing import Protocol

Lonlat = tuple[float, float]


class RouteNotFound(Exception):
    """OSRM answered but has no route (NoRoute / NoSegment)."""


class RoutingUnavailable(Exception):
    """OSRM could not be reached or answered with an unexpected error."""


class RoutingTimeout(RoutingUnavailable):
    """OSRM did not answer within the configured timeout."""


class MatrixTooLarge(Exception):
    """More distinct coordinates than the OSRM server accepts (--max-table-size)."""


class Profile(StrEnum):
    CAR = "car"
    MOTORBIKE = "motorbike"


@dataclass(frozen=True)
class RoutingPolicy:
    """Routing rules every request follows. `routing_version` names the road graph,
    so cached answers of another graph are never reused."""

    exclude: tuple[str, ...] = ()
    routing_version: str = "unversioned"

    def key(self) -> str:
        raw = json.dumps({"exclude": sorted(self.exclude), "routing_version": self.routing_version})
        return hashlib.sha256(raw.encode()).hexdigest()[:12]


@dataclass(frozen=True)
class Route:
    distance_m: float
    duration_s: float
    snap_m: tuple[float, ...]  # one per input coordinate, in request order


@dataclass(frozen=True)
class Matrix:
    """distance_m[i][j] / duration_s[i][j]: sources[i] -> destinations[j]; None = no road."""

    distance_m: tuple[tuple[float | None, ...], ...]
    duration_s: tuple[tuple[float | None, ...], ...]
    source_snap_m: tuple[float, ...]
    destination_snap_m: tuple[float, ...]
    stats: dict[str, float] = field(default_factory=dict, compare=False)

    def routable(self, i: int, j: int) -> bool:
        return self.distance_m[i][j] is not None and self.duration_s[i][j] is not None


class RoutingProvider(Protocol):
    def route(self, profile: Profile, origin: Lonlat, destination: Lonlat,
              waypoints: tuple[Lonlat, ...] = ()) -> Route: ...

    def matrix(self, profile: Profile, sources: list[Lonlat], destinations: list[Lonlat]) -> Matrix: ...
