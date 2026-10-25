"""pricing module table `pricing_configs` (Revision 9, Section 54;
MVP_CONFIG_BASELINE_V1 Section 5: `pricing_configs (version, service_code,
params_json, active_from)`).

Rows are immutable: a database trigger (see migration) rejects UPDATE and
DELETE. Any parameter change must be a new `version` (Baseline Section 5.1).
`config_baseline_version` and `source_sha256` are TECHNICAL ADDITIONS that make
each row traceable to the YAML it was seeded from.
"""

from datetime import datetime
from typing import Any

from sqlalchemy import DateTime, PrimaryKeyConstraint, String, func
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base
from app.db.types import SERVICE_CODES, in_check


class PricingConfig(Base):
    __tablename__ = "pricing_configs"

    version: Mapped[str] = mapped_column(String(64), nullable=False)
    service_code: Mapped[str] = mapped_column(String(32), nullable=False)
    params_json: Mapped[Any] = mapped_column(JSONB, nullable=False)
    active_from: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)

    config_baseline_version: Mapped[str] = mapped_column(String(64), nullable=False)
    source_sha256: Mapped[str] = mapped_column(String(64), nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )

    __table_args__ = (
        PrimaryKeyConstraint("version", "service_code"),
        in_check("service_code", SERVICE_CODES, "service_code"),
    )
