"""Survey S1 endpoints - DRAFT, development only (owner decision P1-D5).

Respondents are anonymous: these endpoints take no application account and
never link answers to `users`. Export and quota are ADMIN-only.
"""

import uuid
from pathlib import Path
from typing import Any, Literal

from fastapi import APIRouter, Depends, Response, status
from fastapi.responses import HTMLResponse
from sqlalchemy.orm import Session

from app.core.settings import Settings, get_settings
from app.db.session import get_db
from app.modules.identity.deps import User, require_roles
from app.modules.ml_models import survey_service
from app.modules.ml_models.survey_schemas import SubmitIn

router = APIRouter(tags=["survey-s1 (draft)"])
FORM = Path(__file__).parent / "static" / "survey_s1.html"


@router.get("/survey/s1", response_class=HTMLResponse, include_in_schema=False)
def form() -> str:
    return FORM.read_text(encoding="utf-8")


@router.post("/api/survey/s1/sessions", status_code=status.HTTP_201_CREATED)
def start(session: Session = Depends(get_db), settings: Settings = Depends(get_settings)) -> dict[str, Any]:
    r = survey_service.start_session(session, settings)
    return {"respondent_id": r.respondent_id, "dataset": r.dataset, "questionnaire_version": r.questionnaire_version,
            "status": "DRAFT_NOT_RELEASED", "design": r.design_json}


@router.post("/api/survey/s1/sessions/{respondent_id}/submit", status_code=status.HTTP_201_CREATED)
def submit(respondent_id: uuid.UUID, body: SubmitIn, session: Session = Depends(get_db),
           settings: Settings = Depends(get_settings)) -> dict[str, Any]:
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
