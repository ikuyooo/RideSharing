"""pricing service - read access to the versioned `pricing_configs` (Baseline Section 5).

`active_sections` returns the raw baseline sections of one row (Phase 2); `load_pricing`
returns the validated, typed parameters of all five services of one pricing_version (Phase 3).
Rows are immutable (a database trigger rejects UPDATE and DELETE; a parameter change is a new
version - Baseline 5.1), so both caches can never be stale."""

from typing import Any

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.errors import ApiError
from app.db.types import SERVICE_CODES
from app.modules.pricing.models import PricingConfig
from app.modules.pricing.params import PricingConfigError, PricingParams

_SECTIONS: dict[tuple[str, str], dict[str, Any]] = {}
_PARAMS: dict[str, PricingParams] = {}


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


def load_pricing(session: Session, version: str) -> PricingParams:
    """Typed parameters of `version`, built only from its `pricing_configs` rows (one per service).
    A section shared by several rows (car_urban, car_intercity_private) must be identical in each."""
    if version not in _PARAMS:
        rows = session.execute(select(PricingConfig.service_code, PricingConfig.params_json)
                               .where(PricingConfig.version == version)).tuples().all()
        missing = set(SERVICE_CODES) - {code for code, _ in rows}
        if missing:
            raise ApiError(503, "PRICING_NOT_CONFIGURED", f"pricing_configs {version} lacks {sorted(missing)}")
        sections: dict[str, Any] = {}
        policies = set()
        for _, params in rows:
            policies.add(params["pool_policy_version"])
            for name, body in params["sections"].items():
                if name in sections and sections[name] != body:
                    raise PricingConfigError(f"{version}: section {name} differs between service rows")
                sections[name] = body
        if len(policies) != 1:
            raise PricingConfigError(f"{version}: rows disagree on pool_policy_version")
        _PARAMS[version] = PricingParams.from_sections(version, policies.pop(), sections)
    return _PARAMS[version]
