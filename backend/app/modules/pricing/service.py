"""pricing service - read access to the versioned `pricing_configs` (Baseline Section 5).
Phase 3 adds the pool allocation; Phase 2 only reads the active parameters."""

from typing import Any

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.errors import ApiError
from app.modules.pricing.models import PricingConfig


_SECTIONS: dict[tuple[str, str], dict[str, Any]] = {}


def active_sections(session: Session, service_code: str, version: str) -> dict[str, Any]:
    """Baseline sections of `version` (the configured pricing_version) for one service.

    Cached per process: a (version, service_code) row is immutable - a database trigger rejects
    UPDATE and DELETE, and a parameter change is a new version (Baseline Section 5.1) - so a
    cached row can never be stale. A missing row is not cached."""
    key = (version, service_code)
    if key not in _SECTIONS:
        params = session.scalar(select(PricingConfig.params_json)
                                .where(PricingConfig.service_code == service_code, PricingConfig.version == version))
        if params is None:
            raise ApiError(503, "PRICING_NOT_CONFIGURED", f"pricing_configs has no {version} row for {service_code}")
        _SECTIONS[key] = params["sections"]
    return _SECTIONS[key]
