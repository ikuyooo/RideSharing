"""p1 service area excluded layer

GEO-03 / GEO-04 (owner decision "PHASE 1 FINAL CLOSURE"): a service-area version
may carry an `EXCLUDED` geometry next to URBAN / TOTAL - the parts of the raw
administrative TOTAL polygon that cannot be served (no routable road inside, or
no car route from the anchor). The raw TOTAL polygon is kept unchanged; the
accept-able area is TOTAL minus EXCLUDED. `area_type` is VARCHAR(8), so
'EXCLUDED' fits without a type change.

Revision ID: 0003
Revises: 0002
Create Date: 2026-10-27 09:00:00
"""

from collections.abc import Sequence

from alembic import op

revision: str = '0003'
down_revision: str | None = '0002'
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.drop_constraint(op.f('ck_service_areas_area_type'), 'service_areas', type_='check')
    op.create_check_constraint(op.f('ck_service_areas_area_type'), 'service_areas',
                               "area_type IN ('URBAN', 'TOTAL', 'EXCLUDED')")


def downgrade() -> None:
    op.execute("DELETE FROM service_areas WHERE area_type = 'EXCLUDED'")
    op.drop_constraint(op.f('ck_service_areas_area_type'), 'service_areas', type_='check')
    op.create_check_constraint(op.f('ck_service_areas_area_type'), 'service_areas', "area_type IN ('URBAN', 'TOTAL')")
