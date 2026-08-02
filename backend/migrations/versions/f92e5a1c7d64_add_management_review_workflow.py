"""add management review workflow

Revision ID: f92e5a1c7d64
Revises: e71c4d9a2f30
Create Date: 2026-08-02 10:30:00

"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "f92e5a1c7d64"
down_revision: str | Sequence[str] | None = "e71c4d9a2f30"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column(
        "ingestion_records",
        sa.Column(
            "review_status",
            sa.String(length=20),
            server_default="not_required",
            nullable=False,
        ),
    )
    op.add_column("ingestion_records", sa.Column("reviewed_at", sa.DateTime()))
    op.execute(
        """
        UPDATE ingestion_records ir
        JOIN listing_match_records lm ON lm.ingestion_record_id = ir.id
        SET ir.review_status = 'pending'
        WHERE lm.decision = 'review_required'
        """
    )
    op.create_table(
        "ingestion_review_audits",
        sa.Column("id", sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column("public_id", sa.String(length=36), nullable=False),
        sa.Column("ingestion_record_id", sa.BigInteger(), nullable=False),
        sa.Column("action", sa.String(length=20), nullable=False),
        sa.Column("reviewer_name", sa.String(length=80), nullable=False),
        sa.Column("reason", sa.String(length=500), nullable=False),
        sa.Column("previous_decision", sa.String(length=24), nullable=False),
        sa.Column("target_canonical_listing_id", sa.BigInteger()),
        sa.Column("changes", sa.JSON(), nullable=False),
        sa.Column(
            "created_at", sa.DateTime(), server_default=sa.text("CURRENT_TIMESTAMP"), nullable=False
        ),
        sa.Column(
            "updated_at", sa.DateTime(), server_default=sa.text("CURRENT_TIMESTAMP"), nullable=False
        ),
        sa.ForeignKeyConstraint(
            ["ingestion_record_id"], ["ingestion_records.id"], ondelete="CASCADE"
        ),
        sa.ForeignKeyConstraint(
            ["target_canonical_listing_id"], ["canonical_listings.id"], ondelete="SET NULL"
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("public_id"),
    )
    op.create_index(
        "ix_ingestion_review_audits_record_created",
        "ingestion_review_audits",
        ["ingestion_record_id", "created_at"],
    )


def downgrade() -> None:
    op.drop_index(
        "ix_ingestion_review_audits_record_created",
        table_name="ingestion_review_audits",
    )
    op.drop_table("ingestion_review_audits")
    op.drop_column("ingestion_records", "reviewed_at")
    op.drop_column("ingestion_records", "review_status")
