"""Anti-spam for the public survey endpoints (owner decision "PHASE 1 FINAL
CLOSURE", survey infrastructure): a fixed-window rate limit per client.

The client address is never stored or logged. Redis only holds counters keyed by
HMAC(secret, day | address) truncated to 16 hex characters; the day in the HMAC
input rotates the key daily and every counter expires with its window. If Redis
cannot be reached the endpoints refuse (fail closed) rather than run unprotected.

Rule R3 adjustment (owner "DEVELOPMENT FIRST"): rejected submissions (422) are
counted per UTC day and error code only - no address, no request content - so a
form defect on one kind of device shows up during collection. Counting is best
effort: a Redis failure never changes the response the client gets.
"""

import hashlib
import hmac
import logging
from datetime import UTC, datetime, timedelta
from typing import Protocol

import redis

from app.core.errors import ApiError

log = logging.getLogger(__name__)
REJECTION_TTL_S = 90 * 86400


class RateLimiter(Protocol):
    def allow(self, bucket: str, client: str, limit: int, window_s: int) -> bool: ...


class RejectionCounter(Protocol):
    def record(self, code: str) -> None: ...

    def counts(self, days: int) -> dict[str, dict[str, int]]: ...


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


class RedisRejectionCounter:
    def __init__(self, url: str, timeout_s: float) -> None:
        self._client = redis.Redis.from_url(url, socket_timeout=timeout_s, socket_connect_timeout=timeout_s,
                                            decode_responses=True)

    @staticmethod
    def _key(day: datetime) -> str:
        return f"s1:rej:{day:%Y-%m-%d}"

    def record(self, code: str) -> None:
        key = self._key(datetime.now(UTC))
        try:
            pipe = self._client.pipeline()
            pipe.hincrby(key, code, 1)
            pipe.expire(key, REJECTION_TTL_S)
            pipe.execute()
        except redis.RedisError:
            log.warning("survey rejection counter unavailable; code %s not counted", code)

    def counts(self, days: int) -> dict[str, dict[str, int]]:
        today = datetime.now(UTC)
        out = {}
        try:
            for n in range(days):
                day = today - timedelta(days=n)
                if row := self._client.hgetall(self._key(day)):
                    out[f"{day:%Y-%m-%d}"] = {k: int(v) for k, v in sorted(row.items())}
        except redis.RedisError as exc:
            raise ApiError(503, "SURVEY_PROTECTION_UNAVAILABLE", "Rejection counters are unavailable") from exc
        return out
