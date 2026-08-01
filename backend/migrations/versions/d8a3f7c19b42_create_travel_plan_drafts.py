"""create travel plan drafts

Revision ID: d8a3f7c19b42
Revises: c43b2f1d8a20
Create Date: 2026-08-01 17:00:00

"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "d8a3f7c19b42"
down_revision: str | Sequence[str] | None = "c43b2f1d8a20"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "travel_plan_drafts",
        sa.Column("id", sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column("public_id", sa.String(length=36), nullable=False),
        sa.Column("recommendation_session_id", sa.BigInteger(), nullable=False),
        sa.Column("city", sa.String(length=64), nullable=False),
        sa.Column("check_in", sa.Date(), nullable=False),
        sa.Column("check_out", sa.Date(), nullable=False),
        sa.Column("guest_count", sa.Integer(), nullable=False),
        sa.Column("status", sa.String(length=20), nullable=False),
        sa.Column("provider", sa.String(length=32), nullable=False),
        sa.Column("model", sa.String(length=64), nullable=False),
        sa.Column("prompt_tokens", sa.Integer()),
        sa.Column("completion_tokens", sa.Integer()),
        sa.Column("total_tokens", sa.Integer()),
        sa.Column("error_code", sa.String(length=40)),
        sa.Column("summary", sa.Text(), nullable=False),
        sa.Column("payload", sa.JSON(), nullable=False),
        sa.Column(
            "created_at", sa.DateTime(), server_default=sa.text("CURRENT_TIMESTAMP"), nullable=False
        ),
        sa.Column(
            "updated_at", sa.DateTime(), server_default=sa.text("CURRENT_TIMESTAMP"), nullable=False
        ),
        sa.ForeignKeyConstraint(
            ["recommendation_session_id"],
            ["recommendation_sessions.id"],
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("public_id"),
        sa.UniqueConstraint("recommendation_session_id"),
    )
    op.create_index(
        "ix_travel_plan_drafts_city_created",
        "travel_plan_drafts",
        ["city", "created_at"],
    )


def downgrade() -> None:
    op.drop_index("ix_travel_plan_drafts_city_created", table_name="travel_plan_drafts")
    op.drop_table("travel_plan_drafts")
