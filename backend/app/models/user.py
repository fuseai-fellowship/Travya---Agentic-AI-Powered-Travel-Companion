import uuid
from datetime import datetime

from sqlmodel import Field

from app.models.base import Table, created_at_field, id_field, updated_at_field


class User(Table, table=True):
    """Local profile for a Firebase user, created on first authenticated request."""

    __tablename__ = "users"

    id: uuid.UUID = id_field()
    firebase_uid: str = Field(max_length=128, unique=True, index=True)
    email: str | None = Field(default=None, max_length=320)
    display_name: str | None = Field(default=None, max_length=120)
    is_anonymous: bool = False
    home_city: str | None = Field(default=None, max_length=120)
    currency: str = Field(default="USD", min_length=3, max_length=3)
    created_at: datetime = created_at_field()
    updated_at: datetime = updated_at_field()
