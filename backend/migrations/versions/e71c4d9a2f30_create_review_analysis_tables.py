"""create review analysis tables

Revision ID: e71c4d9a2f30
Revises: d8a3f7c19b42
Create Date: 2026-08-01 18:00:00

"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "e71c4d9a2f30"
down_revision: str | Sequence[str] | None = "d8a3f7c19b42"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "listing_reviews",
        sa.Column("id", sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column("canonical_listing_id", sa.BigInteger(), nullable=False),
        sa.Column("platform_code", sa.String(length=32), nullable=False),
        sa.Column("external_id", sa.String(length=128), nullable=False),
        sa.Column("content", sa.String(length=2000), nullable=False),
        sa.Column("rating", sa.Numeric(precision=3, scale=2)),
        sa.Column("review_date", sa.Date()),
        sa.Column("source_url", sa.String(length=1024)),
        sa.Column("language", sa.String(length=16), nullable=False),
        sa.Column("status", sa.String(length=20), nullable=False),
        sa.Column(
            "created_at", sa.DateTime(), server_default=sa.text("CURRENT_TIMESTAMP"), nullable=False
        ),
        sa.Column(
            "updated_at", sa.DateTime(), server_default=sa.text("CURRENT_TIMESTAMP"), nullable=False
        ),
        sa.ForeignKeyConstraint(
            ["canonical_listing_id"], ["canonical_listings.id"], ondelete="CASCADE"
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint(
            "canonical_listing_id", "platform_code", "external_id", name="review_source_identity"
        ),
    )
    op.create_index(
        "ix_listing_reviews_listing_date",
        "listing_reviews",
        ["canonical_listing_id", "review_date"],
    )
    op.create_table(
        "review_analysis_snapshots",
        sa.Column("id", sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column("public_id", sa.String(length=36), nullable=False),
        sa.Column("canonical_listing_id", sa.BigInteger(), nullable=False),
        sa.Column("review_count", sa.Integer(), nullable=False),
        sa.Column("provider", sa.String(length=32), nullable=False),
        sa.Column("model", sa.String(length=64), nullable=False),
        sa.Column("prompt_tokens", sa.Integer()),
        sa.Column("completion_tokens", sa.Integer()),
        sa.Column("total_tokens", sa.Integer()),
        sa.Column("error_code", sa.String(length=40)),
        sa.Column("summary", sa.Text(), nullable=False),
        sa.Column("topics", sa.JSON(), nullable=False),
        sa.Column("sentiment_distribution", sa.JSON(), nullable=False),
        sa.Column("warnings", sa.JSON(), nullable=False),
        sa.Column(
            "created_at", sa.DateTime(), server_default=sa.text("CURRENT_TIMESTAMP"), nullable=False
        ),
        sa.Column(
            "updated_at", sa.DateTime(), server_default=sa.text("CURRENT_TIMESTAMP"), nullable=False
        ),
        sa.ForeignKeyConstraint(
            ["canonical_listing_id"], ["canonical_listings.id"], ondelete="CASCADE"
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("public_id"),
    )
    op.create_index(
        "ix_review_analysis_listing_created",
        "review_analysis_snapshots",
        ["canonical_listing_id", "created_at"],
    )


def downgrade() -> None:
    op.drop_index("ix_review_analysis_listing_created", table_name="review_analysis_snapshots")
    op.drop_table("review_analysis_snapshots")
    op.drop_index("ix_listing_reviews_listing_date", table_name="listing_reviews")
    op.drop_table("listing_reviews")
