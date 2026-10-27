"""ml_models module - survey S1 storage (Revision 9 Section 54 lists
`survey_responses` under ml_models; Sections 59.2 and 65).

Anonymity by construction: no user_id / FK to `users`, no IP, no free text,
timestamps truncated to the minute; the completion time needed by QC2 is kept
only as a duration in seconds (computed from a signed start token, migration 0004). `dataset` separates TEST data (development)
from RESEARCH data (only after the owner releases the survey).
`survey_respondents` is a TECHNICAL ADDITION (one row per respondent: design
shown + demographics); `survey_responses` holds one row per answered item.
"""

import uuid
from datetime import datetime
from typing import Any

from sqlalchemy import BigInteger, CheckConstraint, DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.dialects.postgresql import ARRAY, JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base
from app.db.types import in_check

DATASETS = ("TEST", "RESEARCH")
GROUPS = ("STUDENT", "WORKER")
PARTS = ("1A", "1B", "2")


class SurveyRespondent(Base):
    __tablename__ = "survey_respondents"

    respondent_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True)
    dataset: Mapped[str] = mapped_column(String(16), nullable=False)
    survey_id: Mapped[str] = mapped_column(String(16), nullable=False)
    questionnaire_version: Mapped[str] = mapped_column(String(64), nullable=False)
    design_block: Mapped[int] = mapped_column(Integer, nullable=False)
    design_json: Mapped[Any] = mapped_column(JSONB, nullable=False)
    respondent_group: Mapped[str | None] = mapped_column(String(16))
    demographics_json: Mapped[Any | None] = mapped_column(JSONB)
    started_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    quality_flags: Mapped[list[str] | None] = mapped_column(ARRAY(Text))
    duration_s: Mapped[int | None] = mapped_column(Integer)  # submit - start, seconds (QC2)

    __table_args__ = (
        in_check("dataset", DATASETS, "dataset"),
        in_check("respondent_group", GROUPS, "respondent_group"),
        CheckConstraint("duration_s IS NULL OR duration_s >= 0", name="duration_non_negative"),
    )


class SurveyResponse(Base):
    __tablename__ = "survey_responses"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    respondent_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("survey_respondents.respondent_id", ondelete="CASCADE"), nullable=False, index=True
    )
    part: Mapped[str] = mapped_column(String(4), nullable=False)
    item_id: Mapped[str] = mapped_column(String(64), nullable=False)
    answer_json: Mapped[Any] = mapped_column(JSONB, nullable=False)

    __table_args__ = (in_check("part", PARTS, "part"),)
