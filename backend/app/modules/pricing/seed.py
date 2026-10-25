"""Seed `pricing_configs` with the approved baseline version (owner decision P1-D7).

One `pricing_version` maps to one row per service code (Baseline Section 5:
`pricing_configs (version, service_code, params_json, active_from)`).
`params_json` holds the baseline YAML section(s) that service reads, copied
verbatim, so every row can be compared back to `config/mvp_config_baseline_v1.yaml`.

Idempotent and non-destructive: existing identical rows are left alone; an
existing row with different content aborts the seed (rows are immutable, and a
parameter change requires a new version - Baseline Section 5.1).

Run: python -m app.modules.pricing.seed
"""

import hashlib
import json
from collections.abc import Mapping
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Any
from zoneinfo import ZoneInfo

import yaml
from sqlalchemy import select
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.orm import Session

from app.modules.pricing.models import PricingConfig

# Which baseline YAML sections each service's pricing reads. CAR_URBAN_PRIVATE
# and CAR_URBAN_POOL share `car_urban` (Appendix B: "Dùng chung cho
# CAR_URBAN_PRIVATE và CAR_URBAN_POOL"); CAR_INTERCITY_POOL derives its
# SeatReference from the intercity private fare (Section 28.1).
SERVICE_SECTIONS: dict[str, tuple[str, ...]] = {
    "BIKE_URBAN": ("bike_urban",),
    "CAR_URBAN_PRIVATE": ("car_urban",),
    "CAR_URBAN_POOL": ("car_urban",),
    "CAR_INTERCITY_PRIVATE": ("car_intercity_private",),
    "CAR_INTERCITY_POOL": ("car_intercity_pool", "car_intercity_private"),
}

# Baseline status line: "LOCKED & APPROVED ... Ngày 23/10/2026".
BASELINE_APPROVED_AT = datetime(2026, 10, 23, tzinfo=ZoneInfo("Asia/Ho_Chi_Minh"))


class PricingSeedConflict(RuntimeError):
    """An existing row for the same (version, service_code) differs from the baseline."""


@dataclass(frozen=True)
class SeedResult:
    inserted: list[str]
    unchanged: list[str]


def canonical_sha256(data: Mapping[str, Any]) -> str:
    return hashlib.sha256(json.dumps(data, sort_keys=True, ensure_ascii=False).encode()).hexdigest()


def expected_rows(baseline: Mapping[str, Any]) -> list[dict[str, Any]]:
    digest = canonical_sha256(baseline)
    rows = []
    for service_code, sections in SERVICE_SECTIONS.items():
        rows.append(
            {
                "version": baseline["pricing_version"],
                "service_code": service_code,
                "params_json": {
                    "pricing_version": baseline["pricing_version"],
                    "pool_policy_version": baseline["pool_policy_version"],
                    "sections": {name: baseline[name] for name in sections},
                },
                "active_from": BASELINE_APPROVED_AT,
                "config_baseline_version": baseline["config_baseline_version"],
                "source_sha256": digest,
            }
        )
    return rows


def seed_pricing_configs(session: Session, baseline: Mapping[str, Any]) -> SeedResult:
    inserted, unchanged = [], []
    for row in expected_rows(baseline):
        stmt = (
            insert(PricingConfig)
            .values(**row)
            .on_conflict_do_nothing(index_elements=["version", "service_code"])
            .returning(PricingConfig.service_code)
        )
        # RETURNING yields a row only when the insert happened (rowcount is not
        # reliable for INSERT ... ON CONFLICT through the ORM session).
        if session.execute(stmt).scalar_one_or_none() is not None:
            inserted.append(row["service_code"])
            continue
        existing = session.scalars(
            select(PricingConfig).where(
                PricingConfig.version == row["version"],
                PricingConfig.service_code == row["service_code"],
            )
        ).one()
        same = (
            existing.params_json == row["params_json"]
            and existing.active_from == row["active_from"]
            and existing.config_baseline_version == row["config_baseline_version"]
            and existing.source_sha256 == row["source_sha256"]
        )
        if not same:
            session.rollback()
            raise PricingSeedConflict(
                f"pricing_configs ({row['version']}, {row['service_code']}) exists with different content; "
                "rows are immutable - a parameter change needs a new pricing_version"
            )
        unchanged.append(row["service_code"])
    session.commit()
    return SeedResult(inserted=inserted, unchanged=unchanged)


def main() -> None:
    from app.core.settings import get_settings
    from app.db.session import get_sessionmaker

    path = Path(get_settings().config_baseline_path)
    baseline = yaml.safe_load(path.read_text(encoding="utf-8"))
    with get_sessionmaker()() as session:
        result = seed_pricing_configs(session, baseline)
    print(f"pricing_configs seed: inserted={result.inserted} unchanged={result.unchanged}")


if __name__ == "__main__":
    main()
