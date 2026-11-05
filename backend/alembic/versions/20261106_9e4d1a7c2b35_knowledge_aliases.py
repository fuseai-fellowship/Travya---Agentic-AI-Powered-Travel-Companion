"""Destination aliases for the guide knowledge base, keyed by the guide page's URL

Revision ID: 9e4d1a7c2b35
Revises: 5b7e2c91d4a8
Create Date: 2026-11-06 11:00:00+00:00
"""

from collections.abc import Sequence

import sqlalchemy as sa
import sqlmodel

from alembic import op

revision: str = "9e4d1a7c2b35"
down_revision: str | None = "5b7e2c91d4a8"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "knowledge_aliases",
        sa.Column("alias", sqlmodel.sql.sqltypes.AutoString(length=200), nullable=False),
        sa.Column("source_url", sqlmodel.sql.sqltypes.AutoString(length=1000), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint("alias"),
    )
    op.create_index(
        op.f("ix_knowledge_aliases_source_url"), "knowledge_aliases", ["source_url"], unique=False
    )


def downgrade() -> None:
    op.drop_index(op.f("ix_knowledge_aliases_source_url"), table_name="knowledge_aliases")
    op.drop_table("knowledge_aliases")
