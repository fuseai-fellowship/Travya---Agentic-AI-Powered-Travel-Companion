import uuid
from datetime import UTC, datetime

from sqlalchemy import DateTime
from sqlmodel import Field, SQLModel


def utcnow() -> datetime:
    return datetime.now(UTC)


def id_field() -> uuid.UUID:
    return Field(default_factory=uuid.uuid4, primary_key=True)


def created_at_field() -> datetime:
    return Field(default_factory=utcnow, sa_type=DateTime(timezone=True), nullable=False)  # type: ignore[call-overload]


def updated_at_field() -> datetime:
    return Field(
        default_factory=utcnow,
        sa_type=DateTime(timezone=True),  # type: ignore[call-overload]
        nullable=False,
        sa_column_kwargs={"onupdate": utcnow},
    )


class Table(SQLModel):
    """Base for all tables."""
