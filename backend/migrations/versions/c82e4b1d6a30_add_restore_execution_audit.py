"""add restore execution audit

Revision ID: c82e4b1d6a30
Revises: b31f0a7c9d22
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "c82e4b1d6a30"
down_revision: str | Sequence[str] | None = "b31f0a7c9d22"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column(
        "archive_restore_requests", sa.Column("executed_by", sa.BigInteger(), nullable=True)
    )
    op.add_column(
        "archive_restore_requests", sa.Column("executed_at", sa.DateTime(), nullable=True)
    )
    op.add_column(
        "archive_restore_requests", sa.Column("execution_summary", sa.JSON(), nullable=True)
    )
    op.create_foreign_key(
        "fk_archive_restore_requests_executed_by_admin_users",
        "archive_restore_requests",
        "admin_users",
        ["executed_by"],
        ["id"],
        ondelete="SET NULL",
    )


def downgrade() -> None:
    op.drop_constraint(
        "fk_archive_restore_requests_executed_by_admin_users",
        "archive_restore_requests",
        type_="foreignkey",
    )
    op.drop_column("archive_restore_requests", "execution_summary")
    op.drop_column("archive_restore_requests", "executed_at")
    op.drop_column("archive_restore_requests", "executed_by")
