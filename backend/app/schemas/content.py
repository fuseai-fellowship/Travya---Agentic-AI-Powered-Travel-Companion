import uuid
from datetime import date, datetime
from typing import Any, Literal

from pydantic import Field

from app.models import FeedbackTarget, MessageRole
from app.schemas.common import ApiModel

NoteColor = Literal["yellow", "pink", "blue", "green", "purple", "orange"]


class MeRead(ApiModel):
    id: uuid.UUID
    email: str | None
    display_name: str | None
    is_anonymous: bool
    is_admin: bool
    home_city: str | None
    currency: str


class MeUpdate(ApiModel):
    display_name: str | None = Field(default=None, max_length=120)
    home_city: str | None = Field(default=None, max_length=120)
    currency: str | None = Field(default=None, pattern=r"^[A-Z]{3}$")


class NoteCreate(ApiModel):
    title: str = Field(min_length=1, max_length=200)
    content: str = Field(default="", max_length=10_000)
    color: NoteColor = "yellow"
    is_pinned: bool = False
    trip_id: uuid.UUID | None = None


class NoteUpdate(ApiModel):
    title: str | None = Field(default=None, min_length=1, max_length=200)
    content: str | None = Field(default=None, max_length=10_000)
    color: NoteColor | None = None
    is_pinned: bool | None = None
    trip_id: uuid.UUID | None = None


class NoteRead(ApiModel):
    id: uuid.UUID
    title: str
    content: str
    color: str
    is_pinned: bool
    trip_id: uuid.UUID | None
    created_at: datetime
    updated_at: datetime


class ConversationCreate(ApiModel):
    title: str | None = Field(default=None, max_length=200)
    trip_id: uuid.UUID | None = None


class ConversationUpdate(ApiModel):
    title: str | None = Field(default=None, min_length=1, max_length=200)
    is_archived: bool | None = None
    is_favorite: bool | None = None
    trip_id: uuid.UUID | None = None


class ConversationRead(ApiModel):
    id: uuid.UUID
    title: str
    trip_id: uuid.UUID | None
    is_archived: bool
    is_favorite: bool
    last_message_at: datetime
    created_at: datetime


class MessageRead(ApiModel):
    id: uuid.UUID
    role: MessageRole
    content: str
    meta: dict[str, Any]
    created_at: datetime


class ChatRequest(ApiModel):
    content: str = Field(min_length=1, max_length=4000)


class DocumentRead(ApiModel):
    id: uuid.UUID
    trip_id: uuid.UUID | None
    filename: str
    content_type: str
    size_bytes: int
    created_at: datetime


class DownloadLink(ApiModel):
    url: str
    expires_in: int


class FeedbackCreate(ApiModel):
    target_type: FeedbackTarget
    target_id: uuid.UUID
    rating: int = Field(ge=1, le=5)
    comment: str | None = Field(default=None, max_length=1000)


class FeedbackRead(FeedbackCreate):
    id: uuid.UUID
    created_at: datetime


class WeatherDay(ApiModel):
    day: date
    temp_min_c: float
    temp_max_c: float
    precipitation_mm: float
    precipitation_probability: int | None
    weather_code: int
    summary: str
    is_climate_estimate: bool


class PlaceSuggestion(ApiModel):
    name: str
    display_name: str
    lat: float
    lon: float
    category: str | None
    country_code: str | None


class GuideRead(ApiModel):
    destination: str
    summary: str
    sections: list[dict[str, str]]
    url: str
    source: str
    license: str


class UsageRead(ApiModel):
    llm_runs_remaining_today: int
