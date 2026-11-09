"""add review fields to documents

Revision ID: d47607e6f52d
Revises: 43bac6f972ed
Create Date: 2026-11-09 18:00:11.712599

"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = "d47607e6f52d"
down_revision: str | Sequence[str] | None = "43bac6f972ed"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column("documents", sa.Column("reviewed_by", sa.Text(), nullable=True))
    op.add_column(
        "documents", sa.Column("reviewed_at", sa.DateTime(timezone=True), nullable=True)
    )
    op.add_column("documents", sa.Column("rejection_reason", sa.Text(), nullable=True))


def downgrade() -> None:
    op.drop_column("documents", "rejection_reason")
    op.drop_column("documents", "reviewed_at")
    op.drop_column("documents", "reviewed_by")
