"""jobs module table `scheduled_jobs` (Revision 9, Section 55, column list
verbatim). Schema only in Phase 1; the worker is Phase 4."""

import uuid
from datetime import datetime

from sqlalchemy import BigInteger, DateTime, Index, Integer, String, Text, func, text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base
from app.db.types import in_check

JOB_STATUSES = ("PENDING", "PROCESSING", "COMPLETED", "COMPLETED_NOOP", "FAILED_RETRY", "DEAD_LETTER")


class ScheduledJob(Base):
    __tablename__ = "scheduled_jobs"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    job_type: Mapped[str] = mapped_column(String(64), nullable=False)
    target_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), nullable=False)
    run_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    status: Mapped[str] = mapped_column(String(24), nullable=False, server_default="PENDING")
    attempts: Mapped[int] = mapped_column(Integer, nullable=False, server_default="0")
    max_attempts: Mapped[int] = mapped_column(Integer, nullable=False, server_default="5")
    last_error: Mapped[str | None] = mapped_column(Text)
    idempotency_key: Mapped[str] = mapped_column(String(128), nullable=False, unique=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )

    __table_args__ = (
        in_check("status", JOB_STATUSES, "status"),
        # Section 56.2 (verbatim name and predicate).
        Index(
            "idx_scheduled_jobs_due",
            "run_at",
            postgresql_where=text("status IN ('PENDING', 'FAILED_RETRY')"),
        ),
    )
