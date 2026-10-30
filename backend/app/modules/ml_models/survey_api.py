"""Survey S1 endpoints - DRAFT, development only (owner decision P1-D5).

Respondents are anonymous: these endpoints take no application account and
never link answers to `users`. Export and quota are ADMIN-only.
"""

import uuid
from collections.abc import Callable, Coroutine
from pathlib import Path
from typing import Any, Literal

from fastapi import APIRouter, Depends, Query, Request, Response, status
from fastapi.exceptions import RequestValidationError
from fastapi.responses import HTMLResponse
from fastapi.routing import APIRoute
from sqlalchemy.orm import Session

from app.core.errors import ApiError
from app.core.settings import Settings, get_settings
from app.db.session import get_db
from app.modules.identity.deps import User, require_roles
from app.modules.ml_models import survey_service
from app.modules.ml_models.survey_guard import RateLimiter, RedisRateLimiter, RedisRejectionCounter, RejectionCounter
from app.modules.ml_models.survey_schemas import StartIn, SubmitIn

FORM = Path(__file__).parent / "static" / "survey_s1.html"
PUBLIC_PREFIX = "/api/survey/s1/"


def get_rejection_counter(settings: Settings = Depends(get_settings)) -> RejectionCounter:
    """Overridable in tests; production keeps aggregate counters in Redis (rule R3)."""
    return RedisRejectionCounter(settings.redis_url, settings.dependency_timeout_s)


class CountRejectionsRoute(APIRoute):
    """Rule R3: every 422 of a public survey endpoint is counted by error code. Body
    validation runs inside the route handler, so schema rejections are seen here too."""

    def get_route_handler(self) -> Callable[[Request], Coroutine[Any, Any, Response]]:
        handler = super().get_route_handler()

        async def counted(request: Request) -> Response:
            try:
                return await handler(request)
            except (ApiError, RequestValidationError) as exc:
                if request.url.path.startswith(PUBLIC_PREFIX):
                    if isinstance(exc, RequestValidationError):
                        code = "REQUEST_VALIDATION"
                    elif exc.status_code == 422:
                        code = exc.code
                    else:
                        raise
                    factory = request.app.dependency_overrides.get(get_rejection_counter)
                    counter = factory() if factory else get_rejection_counter(get_settings())
                    counter.record(code)
                raise

        return counted


router = APIRouter(tags=["survey-s1 (draft)"], route_class=CountRejectionsRoute)


@router.get("/survey/s1", response_class=HTMLResponse, include_in_schema=False)
def form() -> str:
    return FORM.read_text(encoding="utf-8")


def get_rate_limiter(settings: Settings = Depends(get_settings)) -> RateLimiter:
    """Overridable in tests; production keeps salted-hash counters in Redis."""
    return RedisRateLimiter(settings.redis_url, settings.jwt_secret, settings.dependency_timeout_s)


def _limit(request: Request, limiter: RateLimiter, bucket: str, per_hour: int) -> None:
    # Behind the HTTPS proxy uvicorn runs with --proxy-headers, so request.client is
    # the real client; the address is only hashed (survey_guard), never stored.
    client = request.client.host if request.client else "unknown"
    if not limiter.allow(bucket, client, per_hour, 3600):
        raise ApiError(429, "RATE_LIMITED", "Too many requests, please try again later")


@router.post("/api/survey/s1/sessions", status_code=status.HTTP_201_CREATED)
def start(body: StartIn, request: Request, session: Session = Depends(get_db),
          settings: Settings = Depends(get_settings), limiter: RateLimiter = Depends(get_rate_limiter)) -> dict[str, Any]:
    _limit(request, limiter, "start", settings.survey_rate_limit_starts_per_hour)
    r, token = survey_service.start_session(session, settings, body)
    return {"respondent_id": r.respondent_id, "dataset": r.dataset, "questionnaire_version": r.questionnaire_version,
            "status": "DRAFT_NOT_RELEASED", "design": r.design_json, "start_token": token,
            "demographics_options": survey_service.demographics_options(settings)}


@router.post("/api/survey/s1/sessions/{respondent_id}/submit", status_code=status.HTTP_201_CREATED)
def submit(respondent_id: uuid.UUID, body: SubmitIn, request: Request, session: Session = Depends(get_db),
           settings: Settings = Depends(get_settings), limiter: RateLimiter = Depends(get_rate_limiter)) -> dict[str, Any]:
    _limit(request, limiter, "submit", settings.survey_rate_limit_submits_per_hour)
    r = survey_service.submit(session, settings, respondent_id, body)
    return {"respondent_id": r.respondent_id, "quality_flags": r.quality_flags}


@router.get("/api/admin/survey/s1/export/{table}")
def export(table: Literal["respondents", "choices", "fairness_h4"], dataset: Literal["TEST", "RESEARCH"],
           _: User = Depends(require_roles("ADMIN")), session: Session = Depends(get_db)) -> Response:
    body = survey_service.export_table(session, dataset, table)
    return Response(content=body, media_type="text/csv; charset=utf-8",
                    headers={"Content-Disposition": f'attachment; filename="s1_{dataset.lower()}_{table}.csv"'})


@router.get("/api/admin/survey/s1/quota")
def quota(dataset: Literal["TEST", "RESEARCH"], _: User = Depends(require_roles("ADMIN")),
          session: Session = Depends(get_db), settings: Settings = Depends(get_settings)) -> dict[str, Any]:
    return survey_service.quota(session, dataset, settings)


@router.get("/api/admin/survey/s1/rejections")
def rejections(days: int = Query(14, ge=1, le=90), _: User = Depends(require_roles("ADMIN")),
               counter: RejectionCounter = Depends(get_rejection_counter)) -> dict[str, Any]:
    """Rule R3: daily 422 counts by error code (aggregate only - no address, no content)."""
    by_day = counter.counts(days)
    total: dict[str, int] = {}
    for row in by_day.values():
        for code, n in row.items():
            total[code] = total.get(code, 0) + n
    return {"days": days, "by_day": by_day, "total_by_code": dict(sorted(total.items()))}


@router.delete("/api/admin/survey/s1/respondents/{respondent_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_respondent(respondent_id: uuid.UUID, _: User = Depends(require_roles("ADMIN")),
                      session: Session = Depends(get_db)) -> Response:
    """Deletion on request: the respondent quotes the session code shown at the end."""
    survey_service.delete_respondent(session, respondent_id)
    return Response(status_code=status.HTTP_204_NO_CONTENT)
