"""p1 survey s1 duration

Survey decision 7 (owner "PHASE 1 FINAL CLOSURE"): a short completion time is
flagged (QC2), never auto-excluded. The duration is computed at submission from
an HMAC-signed start token, so only whole seconds of duration are stored and the
timestamps stay truncated to the minute.

Revision ID: 0004
Revises: 0003
Create Date: 2026-10-27 12:00:00
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = '0004'
down_revision: str | None = '0003'
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column('survey_respondents', sa.Column('duration_s', sa.Integer(), nullable=True))
    op.create_check_constraint(op.f('ck_survey_respondents_duration_non_negative'), 'survey_respondents',
                               'duration_s IS NULL OR duration_s >= 0')


def downgrade() -> None:
    op.drop_constraint(op.f('ck_survey_respondents_duration_non_negative'), 'survey_respondents', type_='check')
    op.drop_column('survey_respondents', 'duration_s')
