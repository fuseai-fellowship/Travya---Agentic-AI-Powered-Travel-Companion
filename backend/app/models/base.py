import uuid
from datetime import UTC, datetime
from typing import Any

from sqlalchemy import DateTime
from sqlmodel import Field, SQLModel


def utcnow() -> datetime:
    return datetime.now(UTC)


def id_field() -> Any:
    return Field(default_factory=uuid.uuid4, primary_key=True)


def created_at_field() -> Any:
    return Field(default_factory=utcnow, sa_type=DateTime(timezone=True), nullable=False)


def updated_at_field() -> Any:
    return Field(
        default_factory=utcnow,
        sa_type=DateTime(timezone=True),
        nullable=False,
        sa_column_kwargs={"onupdate": utcnow},
    )


class Table(SQLModel):
    """Base for all tables."""
