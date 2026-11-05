"""When the current planning run started, so stuck or concurrent runs can be detected

Revision ID: 5b7e2c91d4a8
Revises: 3c1f2a9d7e40
Create Date: 2026-11-06 09:00:00+00:00
"""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

revision: str = "5b7e2c91d4a8"
down_revision: str | None = "3c1f2a9d7e40"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column(
        "trips", sa.Column("planning_started_at", sa.DateTime(timezone=True), nullable=True)
    )


def downgrade() -> None:
    op.drop_column("trips", "planning_started_at")
