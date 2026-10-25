"""Dependency probes used by the readiness endpoint.

Each probe performs a real round-trip (SQL query, PING, routing request) so a
dependency is only reported "ok" when its API actually answers.
"""

import time
from collections.abc import Callable
from typing import Literal

import httpx
import redis
from pydantic import BaseModel
from sqlalchemy import create_engine, text

from app.core.settings import Settings

# Central Hanoi (Hoan Kiem). Used only as a routing liveness probe.
PROBE_LON, PROBE_LAT = 105.8542, 21.0285


class CheckResult(BaseModel):
    status: Literal["ok", "error"]
    latency_ms: float
    detail: str


def _timed(fn: Callable[[], str]) -> CheckResult:
    start = time.perf_counter()
    try:
        detail = fn()
        status: Literal["ok", "error"] = "ok"
    except Exception as exc:  # noqa: BLE001 - surface any dependency failure
        detail = f"{type(exc).__name__}: {exc}"
        status = "error"
    return CheckResult(
        status=status, latency_ms=round((time.perf_counter() - start) * 1000, 2), detail=detail
    )


def check_postgres(settings: Settings) -> CheckResult:
    def probe() -> str:
        engine = create_engine(
            settings.database_url,
            pool_pre_ping=False,
            connect_args={"connect_timeout": int(settings.dependency_timeout_s)},
        )
        try:
            with engine.connect() as conn:
                return f"postgis {conn.execute(text('SELECT postgis_version()')).scalar_one()}"
        finally:
            engine.dispose()

    return _timed(probe)


def check_redis(settings: Settings) -> CheckResult:
    def probe() -> str:
        client = redis.Redis.from_url(
            settings.redis_url,
            socket_timeout=settings.dependency_timeout_s,
            socket_connect_timeout=settings.dependency_timeout_s,
        )
        try:
            if not client.ping():
                raise RuntimeError("PING returned false")
            return "PONG"
        finally:
            client.close()

    return _timed(probe)


def check_osrm(base_url: str, timeout_s: float) -> CheckResult:
    def probe() -> str:
        resp = httpx.get(
            f"{base_url}/nearest/v1/driving/{PROBE_LON},{PROBE_LAT}", timeout=timeout_s
        )
        body = resp.json()
        if resp.status_code != 200 or body.get("code") != "Ok":
            raise RuntimeError(f"HTTP {resp.status_code} code={body.get('code')}")
        return "nearest Ok"

    return _timed(probe)
