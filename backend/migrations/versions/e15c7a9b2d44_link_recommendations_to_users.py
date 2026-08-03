"""link recommendation sessions to users

Revision ID: e15c7a9b2d44
Revises: d94a2f6b8c41
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "e15c7a9b2d44"
down_revision: str | Sequence[str] | None = "d94a2f6b8c41"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column("recommendation_sessions", sa.Column("user_id", sa.BigInteger(), nullable=True))
    op.create_foreign_key(
        "fk_recommendation_sessions_user_id",
        "recommendation_sessions",
        "user_accounts",
        ["user_id"],
        ["id"],
        ondelete="SET NULL",
    )
    op.create_index(
        "ix_recommendation_sessions_user_created",
        "recommendation_sessions",
        ["user_id", "created_at"],
    )


def downgrade() -> None:
    op.drop_index("ix_recommendation_sessions_user_created", table_name="recommendation_sessions")
    op.drop_constraint(
        "fk_recommendation_sessions_user_id", "recommendation_sessions", type_="foreignkey"
    )
    op.drop_column("recommendation_sessions", "user_id")
