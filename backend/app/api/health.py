from fastapi import APIRouter, Depends, Response, status
from pydantic import BaseModel

from app.core.config_baseline import load_config_baseline
from app.core.health import CheckResult, check_osrm, check_postgres, check_redis
from app.core.settings import Settings, get_settings

router = APIRouter(prefix="/health", tags=["health"])


class LiveResponse(BaseModel):
    status: str


class ReadyResponse(BaseModel):
    status: str
    config_baseline_version: str | None
    pricing_version: str | None
    checks: dict[str, CheckResult]


@router.get("/live", response_model=LiveResponse)
def live() -> LiveResponse:
    """The API process is up and serving requests."""
    return LiveResponse(status="ok")


@router.get("/ready", response_model=ReadyResponse)
def ready(response: Response, settings: Settings = Depends(get_settings)) -> ReadyResponse:
    """All Phase 0 dependencies answer real requests; 503 otherwise."""
    timeout = settings.dependency_timeout_s
    checks = {
        "postgres": check_postgres(settings),
        "redis": check_redis(settings),
        "osrm_car": check_osrm(settings.osrm_car_url, timeout),
        "osrm_motorbike": check_osrm(settings.osrm_motorbike_url, timeout),
    }

    baseline_version = pricing_version = None
    try:
        baseline = load_config_baseline(settings.config_baseline_path)
        baseline_version = baseline["config_baseline_version"]
        pricing_version = baseline["pricing_version"]
        checks["config_baseline"] = CheckResult(status="ok", latency_ms=0.0, detail="loaded")
    except Exception as exc:  # noqa: BLE001
        checks["config_baseline"] = CheckResult(
            status="error", latency_ms=0.0, detail=f"{type(exc).__name__}: {exc}"
        )

    all_ok = all(c.status == "ok" for c in checks.values())
    if not all_ok:
        response.status_code = status.HTTP_503_SERVICE_UNAVAILABLE
    return ReadyResponse(
        status="ok" if all_ok else "degraded",
        config_baseline_version=baseline_version,
        pricing_version=pricing_version,
        checks=checks,
    )
