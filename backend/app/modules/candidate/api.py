"""Candidate generation endpoints - Phase 2 TECHNICAL ADDITIONS for testing and the demo,
ADMIN only. The passenger-facing `GET /api/trip-requests/{id}/recommendations` of Section
57 needs pricing (P3) and ranking (P6) and is not exposed in Phase 2."""

import uuid
from typing import Any

from fastapi import APIRouter, Depends, status
from pydantic import BaseModel, ConfigDict
from sqlalchemy.orm import Session

from app.core.settings import Settings, get_settings
from app.db.session import get_db
from app.modules.candidate import service
from app.modules.identity.deps import User, require_roles

router = APIRouter(tags=["candidate (P2, admin)"])


class RunIn(BaseModel):
    model_config = ConfigDict(extra="forbid")

    request_id: uuid.UUID


@router.post("/api/admin/candidates/runs", status_code=status.HTTP_201_CREATED)
def create_run(body: RunIn, _: User = Depends(require_roles("ADMIN")), session: Session = Depends(get_db),
               settings: Settings = Depends(get_settings)) -> dict[str, Any]:
    stored, _result = service.run(session, settings, body.request_id)
    return service.run_out(session, stored.id)


@router.get("/api/admin/candidates/runs/{run_id}")
def get_run(run_id: uuid.UUID, _: User = Depends(require_roles("ADMIN")),
            session: Session = Depends(get_db)) -> dict[str, Any]:
    return service.run_out(session, run_id)
