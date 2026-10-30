"""pricing service - read access to the versioned `pricing_configs` (Baseline Section 5).
Phase 3 adds the pool allocation; Phase 2 only reads the active parameters."""

from typing import Any

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.errors import ApiError
from app.modules.pricing.models import PricingConfig


def active_sections(session: Session, service_code: str, version: str) -> dict[str, Any]:
    """Baseline sections of `version` (the configured pricing_version) for one service."""
    params = session.scalar(select(PricingConfig.params_json)
                            .where(PricingConfig.service_code == service_code, PricingConfig.version == version))
    if params is None:
        raise ApiError(503, "PRICING_NOT_CONFIGURED", f"pricing_configs has no {version} row for {service_code}")
    return params["sections"]
