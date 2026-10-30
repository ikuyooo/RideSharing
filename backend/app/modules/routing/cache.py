"""Redis cache in front of a RoutingProvider (Revision 9 Section 34).

Key = (policy, profile, origin_geohash_7, dest_geohash_7, time_bucket), as Section 34
specifies. The policy part hashes the excluded classes and the road-graph version, so
an answer computed under another policy or graph is never reused. OSRM has no
traffic data here, so the time bucket is the constant "static" until a time-dependent
profile exists.

Scope (P2 plan OD-P2-02): a geohash-7 cell is ~150 m wide, so a cached answer may
belong to a point up to ~150 m away. Only `route()` without waypoints is cached; the
candidate matrices that feed the hard constraints always go to OSRM. A Redis failure
never fails routing: the request goes to OSRM uncached.
"""

import logging

import redis

from app.modules.routing.provider import Lonlat, Matrix, Profile, Route, RoutingPolicy, RoutingProvider

log = logging.getLogger(__name__)
_BASE32 = "0123456789bcdefghjkmnpqrstuvwxyz"
TIME_BUCKET = "static"


def geohash(lon: float, lat: float, precision: int = 7) -> str:
    lat_lo, lat_hi, lon_lo, lon_hi = -90.0, 90.0, -180.0, 180.0
    out, bits, ch, even = [], 0, 0, True
    while len(out) < precision:
        if even:
            mid = (lon_lo + lon_hi) / 2
            ch = (ch << 1) | (lon >= mid)
            lon_lo, lon_hi = (mid, lon_hi) if lon >= mid else (lon_lo, mid)
        else:
            mid = (lat_lo + lat_hi) / 2
            ch = (ch << 1) | (lat >= mid)
            lat_lo, lat_hi = (mid, lat_hi) if lat >= mid else (lat_lo, mid)
        even = not even
        bits += 1
        if bits == 5:
            out.append(_BASE32[ch])
            bits, ch = 0, 0
    return "".join(out)


def cache_key(policy: RoutingPolicy, profile: Profile, origin: Lonlat, destination: Lonlat) -> str:
    return f"rt:{policy.key()}:{profile}:{geohash(*origin)}:{geohash(*destination)}:{TIME_BUCKET}"


class CachedRoutingProvider:
    def __init__(self, inner: RoutingProvider, policy: RoutingPolicy, client: redis.Redis, ttl_s: int) -> None:
        self._inner = inner
        self._policy = policy
        self._client = client
        self._ttl_s = ttl_s
        self.hits = self.misses = 0

    def route(self, profile: Profile, origin: Lonlat, destination: Lonlat,
              waypoints: tuple[Lonlat, ...] = ()) -> Route:
        if waypoints:
            return self._inner.route(profile, origin, destination, waypoints)
        key = cache_key(self._policy, profile, origin, destination)
        try:
            cached = self._client.get(key)
        except redis.RedisError:
            log.warning("routing cache unavailable; asking OSRM directly")
            cached = None
        if cached:
            self.hits += 1
            distance, duration, snap_o, snap_d = (float(x) for x in cached.split(b","))
            return Route(distance_m=distance, duration_s=duration, snap_m=(snap_o, snap_d))
        self.misses += 1
        route = self._inner.route(profile, origin, destination)
        try:
            self._client.set(key, f"{route.distance_m},{route.duration_s},{route.snap_m[0]},{route.snap_m[1]}",
                             ex=self._ttl_s)
        except redis.RedisError:
            log.warning("routing cache unavailable; answer not stored")
        return route

    def matrix(self, profile: Profile, sources: list[Lonlat], destinations: list[Lonlat]) -> Matrix:
        return self._inner.matrix(profile, sources, destinations)  # never cached (OD-P2-02)
