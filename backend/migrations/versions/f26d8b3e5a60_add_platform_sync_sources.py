"""add platform sync sources

Revision ID: f26d8b3e5a60
Revises: e15c7a9b2d44
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "f26d8b3e5a60"
down_revision: str | Sequence[str] | None = "e15c7a9b2d44"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "platform_sync_sources",
        sa.Column("id", sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column("public_id", sa.String(length=36), nullable=False),
        sa.Column("platform_id", sa.Integer(), nullable=False),
        sa.Column("connector_type", sa.String(length=32), nullable=False),
        sa.Column("source_config", sa.JSON(), nullable=False),
        sa.Column("interval_minutes", sa.Integer(), nullable=False),
        sa.Column("status", sa.String(length=20), nullable=False),
        sa.Column("is_enabled", sa.Boolean(), nullable=False),
        sa.Column("last_run_at", sa.DateTime(), nullable=True),
        sa.Column("last_success_at", sa.DateTime(), nullable=True),
        sa.Column("last_error", sa.String(length=500), nullable=True),
        sa.Column(
            "created_at", sa.DateTime(), server_default=sa.text("CURRENT_TIMESTAMP"), nullable=False
        ),
        sa.Column(
            "updated_at", sa.DateTime(), server_default=sa.text("CURRENT_TIMESTAMP"), nullable=False
        ),
        sa.ForeignKeyConstraint(["platform_id"], ["platforms.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("platform_id"),
        sa.UniqueConstraint("public_id"),
    )


def downgrade() -> None:
    op.drop_table("platform_sync_sources")
