"""add recommendation price freshness evidence

Revision ID: c58f7a2d9e10
Revises: a37e9c2b4d51
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "c58f7a2d9e10"
down_revision: str | Sequence[str] | None = "a37e9c2b4d51"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column("recommendation_results", sa.Column("price_captured_at", sa.DateTime()))
    op.add_column(
        "recommendation_results", sa.Column("price_freshness_status", sa.String(16))
    )
    op.add_column("recommendation_results", sa.Column("price_age_minutes", sa.Integer()))


def downgrade() -> None:
    op.drop_column("recommendation_results", "price_age_minutes")
    op.drop_column("recommendation_results", "price_freshness_status")
    op.drop_column("recommendation_results", "price_captured_at")
