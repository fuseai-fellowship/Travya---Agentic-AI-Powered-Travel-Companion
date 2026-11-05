import uuid
from datetime import UTC, datetime
from enum import StrEnum
from typing import Any

from sqlalchemy import DateTime, Enum
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


def enum_type(enum: type[StrEnum]) -> Enum:
    """Stored as VARCHAR holding the enum value (no native PG enum), loaded back as the enum member."""
    return Enum(
        enum,
        native_enum=False,
        create_constraint=False,
        length=16,
        values_callable=lambda members: [m.value for m in members],
    )


class Table(SQLModel):
    """Base for all tables."""
