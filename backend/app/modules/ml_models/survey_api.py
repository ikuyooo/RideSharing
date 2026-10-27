"""Survey S1 endpoints - DRAFT, development only (owner decision P1-D5).

Respondents are anonymous: these endpoints take no application account and
never link answers to `users`. Export and quota are ADMIN-only.
"""

import uuid
from pathlib import Path
from typing import Any, Literal

from fastapi import APIRouter, Depends, Request, Response, status
from fastapi.responses import HTMLResponse
from sqlalchemy.orm import Session

from app.core.errors import ApiError
from app.core.settings import Settings, get_settings
from app.db.session import get_db
from app.modules.identity.deps import User, require_roles
from app.modules.ml_models import survey_service
from app.modules.ml_models.survey_guard import RateLimiter, RedisRateLimiter
from app.modules.ml_models.survey_schemas import StartIn, SubmitIn

router = APIRouter(tags=["survey-s1 (draft)"])
FORM = Path(__file__).parent / "static" / "survey_s1.html"


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


@router.delete("/api/admin/survey/s1/respondents/{respondent_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_respondent(respondent_id: uuid.UUID, _: User = Depends(require_roles("ADMIN")),
                      session: Session = Depends(get_db)) -> Response:
    """Deletion on request: the respondent quotes the session code shown at the end."""
    survey_service.delete_respondent(session, respondent_id)
    return Response(status_code=status.HTTP_204_NO_CONTENT)
