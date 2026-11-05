"""Stored objects for database-backed file storage

Revision ID: 3c1f2a9d7e40
Revises: 8514c84913fe
Create Date: 2026-11-05 14:00:00+00:00
"""

from collections.abc import Sequence

import sqlalchemy as sa
import sqlmodel

from alembic import op

revision: str = "3c1f2a9d7e40"
down_revision: str | None = "8514c84913fe"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "stored_objects",
        sa.Column("key", sqlmodel.sql.sqltypes.AutoString(length=300), nullable=False),
        sa.Column("content_type", sqlmodel.sql.sqltypes.AutoString(length=100), nullable=False),
        sa.Column("data", sa.LargeBinary(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint("key"),
    )


def downgrade() -> None:
    op.drop_table("stored_objects")
