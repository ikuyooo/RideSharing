"""Anti-spam for the public survey endpoints (owner decision "PHASE 1 FINAL
CLOSURE", survey infrastructure): a fixed-window rate limit per client.

The client address is never stored or logged. Redis only holds counters keyed by
HMAC(secret, day | address) truncated to 16 hex characters; the day in the HMAC
input rotates the key daily and every counter expires with its window. If Redis
cannot be reached the endpoints refuse (fail closed) rather than run unprotected.
"""

import hashlib
import hmac
from datetime import UTC, datetime
from typing import Protocol

import redis

from app.core.errors import ApiError


class RateLimiter(Protocol):
    def allow(self, bucket: str, client: str, limit: int, window_s: int) -> bool: ...


def client_key(secret: str, client: str, now: datetime) -> str:
    message = f"{now.astimezone(UTC):%Y-%m-%d}|{client}".encode()
    return hmac.new(secret.encode(), message, hashlib.sha256).hexdigest()[:16]


class RedisRateLimiter:
    def __init__(self, url: str, secret: str, timeout_s: float) -> None:
        self._client = redis.Redis.from_url(url, socket_timeout=timeout_s, socket_connect_timeout=timeout_s)
        self._secret = secret

    def allow(self, bucket: str, client: str, limit: int, window_s: int) -> bool:
        now = datetime.now(UTC)
        key = f"s1:rl:{bucket}:{int(now.timestamp()) // window_s}:{client_key(self._secret, client, now)}"
        try:
            pipe = self._client.pipeline()
            pipe.incr(key)
            pipe.expire(key, window_s)
            count, _ = pipe.execute()
        except redis.RedisError as exc:
            raise ApiError(503, "SURVEY_PROTECTION_UNAVAILABLE",
                           "The survey is temporarily unavailable, please try again later") from exc
        return int(count) <= limit
