"""add ai recommendation explanations

Revision ID: c43b2f1d8a20
Revises: 2e16c8993302
Create Date: 2026-08-01 16:00:00

"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "c43b2f1d8a20"
down_revision: str | Sequence[str] | None = "2e16c8993302"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column(
        "recommendation_sessions",
        sa.Column(
            "explanation_status",
            sa.String(length=20),
            server_default="not_requested",
            nullable=False,
        ),
    )
    op.add_column(
        "recommendation_sessions", sa.Column("explanation_provider", sa.String(length=32))
    )
    op.add_column("recommendation_sessions", sa.Column("explanation_model", sa.String(length=64)))
    op.add_column("recommendation_sessions", sa.Column("explanation_prompt_tokens", sa.Integer()))
    op.add_column(
        "recommendation_sessions", sa.Column("explanation_completion_tokens", sa.Integer())
    )
    op.add_column("recommendation_sessions", sa.Column("explanation_total_tokens", sa.Integer()))
    op.add_column(
        "recommendation_sessions", sa.Column("explanation_error_code", sa.String(length=40))
    )
    op.add_column("recommendation_results", sa.Column("natural_explanation", sa.Text()))
    op.add_column("recommendation_results", sa.Column("explanation_source", sa.String(length=32)))


def downgrade() -> None:
    op.drop_column("recommendation_results", "explanation_source")
    op.drop_column("recommendation_results", "natural_explanation")
    op.drop_column("recommendation_sessions", "explanation_error_code")
    op.drop_column("recommendation_sessions", "explanation_total_tokens")
    op.drop_column("recommendation_sessions", "explanation_completion_tokens")
    op.drop_column("recommendation_sessions", "explanation_prompt_tokens")
    op.drop_column("recommendation_sessions", "explanation_model")
    op.drop_column("recommendation_sessions", "explanation_provider")
    op.drop_column("recommendation_sessions", "explanation_status")
