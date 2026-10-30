"""Builds the process RoutingProvider: OSRM (both profiles) behind the Redis cache."""

import redis

from app.core.settings import Settings
from app.modules.routing.cache import CachedRoutingProvider
from app.modules.routing.osrm import OsrmRoutingProvider
from app.modules.routing.provider import Profile, RoutingPolicy


def policy_for(settings: Settings, exclude: tuple[str, ...]) -> RoutingPolicy:
    """`exclude` comes from the active service area (GEO-E: ("ferry",))."""
    return RoutingPolicy(exclude=tuple(exclude), routing_version=settings.routing_version)


def osrm_provider(settings: Settings, policy: RoutingPolicy) -> OsrmRoutingProvider:
    return OsrmRoutingProvider({Profile.CAR: settings.osrm_car_url, Profile.MOTORBIKE: settings.osrm_motorbike_url},
                               settings.routing_timeout_s, policy, settings.osrm_max_table_size)


def cached_provider(settings: Settings, policy: RoutingPolicy) -> CachedRoutingProvider:
    client = redis.Redis.from_url(settings.redis_url, socket_timeout=settings.dependency_timeout_s,
                                  socket_connect_timeout=settings.dependency_timeout_s)
    return CachedRoutingProvider(osrm_provider(settings, policy), policy, client, settings.routing_cache_ttl_s)
