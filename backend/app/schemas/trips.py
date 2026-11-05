import uuid
from datetime import date, datetime, time
from decimal import Decimal
from typing import Any, Self

from pydantic import MISSING, Field, model_validator

from app.models import BookingKind, BookingStatus, ItemCategory, TripPace, TripStatus
from app.schemas.common import ApiModel

MAX_TRIP_DAYS = 21


class TripBase(ApiModel):
    title: str = Field(min_length=1, max_length=200)
    destination: str = Field(min_length=2, max_length=200)
    origin: str | None = Field(default=None, max_length=200)
    start_date: date
    end_date: date
    travelers: int = Field(default=1, ge=1, le=20)
    budget: Decimal | None = Field(default=None, ge=0, max_digits=12, decimal_places=2)
    currency: str = Field(default="USD", pattern=r"^[A-Z]{3}$")
    pace: TripPace = TripPace.balanced
    interests: list[str] = Field(default_factory=list, max_length=10)
    notes: str | None = Field(default=None, max_length=2000)


def check_dates(start: date, end: date) -> str | None:
    """Why the dates are unusable, or None."""
    if end < start:
        return "end_date must be on or after start_date"
    if (end - start).days + 1 > MAX_TRIP_DAYS:
        return f"Trips can be at most {MAX_TRIP_DAYS} days"
    return None


class TripCreate(TripBase):
    @model_validator(mode="after")
    def _dates(self) -> Self:
        if problem := check_dates(self.start_date, self.end_date):
            raise ValueError(problem)
        return self


class TripUpdate(ApiModel):
    """Omitted fields stay as they are; only nullable columns accept null."""

    title: str | MISSING = Field(default=MISSING, min_length=1, max_length=200)
    origin: str | None = Field(default=None, max_length=200)
    start_date: date | MISSING = MISSING
    end_date: date | MISSING = MISSING
    travelers: int | MISSING = Field(default=MISSING, ge=1, le=20)
    budget: Decimal | None = Field(default=None, ge=0, max_digits=12, decimal_places=2)
    currency: str | MISSING = Field(default=MISSING, pattern=r"^[A-Z]{3}$")
    pace: TripPace | MISSING = MISSING
    interests: list[str] | MISSING = Field(default=MISSING, max_length=10)
    notes: str | None = Field(default=None, max_length=2000)
    status: TripStatus | MISSING = Field(
        default=MISSING, description="Any status but `planning`, which only the agents set"
    )

    @model_validator(mode="after")
    def _not_planning(self) -> Self:
        if self.status == TripStatus.planning:
            raise ValueError("The planning status is set by the agents")
        return self


class TripRead(TripBase):
    id: uuid.UUID
    country_code: str | None
    latitude: float | None
    longitude: float | None
    status: TripStatus
    cover_photo_url: str | None
    planned_at: datetime | None
    created_at: datetime
    updated_at: datetime


class TripDetail(TripRead):
    plan: dict[str, Any] | None


class ItineraryItemBase(ApiModel):
    day: date
    start_time: time | None = None
    end_time: time | None = None
    title: str = Field(min_length=1, max_length=200)
    description: str | None = Field(default=None, max_length=2000)
    category: ItemCategory = ItemCategory.other
    place_name: str | None = Field(default=None, max_length=300)
    latitude: float | None = Field(default=None, ge=-90, le=90)
    longitude: float | None = Field(default=None, ge=-180, le=180)
    estimated_cost: Decimal | None = Field(default=None, ge=0, max_digits=12, decimal_places=2)


class ItineraryItemCreate(ItineraryItemBase):
    position: int | None = None


class ItineraryItemUpdate(ApiModel):
    day: date | MISSING = MISSING
    position: int | MISSING = MISSING
    start_time: time | None = None
    end_time: time | None = None
    title: str | MISSING = Field(default=MISSING, min_length=1, max_length=200)
    description: str | None = Field(default=None, max_length=2000)
    category: ItemCategory | MISSING = MISSING
    place_name: str | None = Field(default=None, max_length=300)
    latitude: float | None = Field(default=None, ge=-90, le=90)
    longitude: float | None = Field(default=None, ge=-180, le=180)
    estimated_cost: Decimal | None = Field(default=None, ge=0, max_digits=12, decimal_places=2)


class ItineraryItemRead(ItineraryItemBase):
    id: uuid.UUID
    trip_id: uuid.UUID
    position: int
    source: str


class BookingRead(ApiModel):
    id: uuid.UUID
    trip_id: uuid.UUID
    kind: BookingKind
    title: str
    provider: str
    details: dict[str, Any]
    amount: Decimal
    currency: str
    status: BookingStatus
    confirmation_code: str | None
    is_simulated: bool
    confirmed_at: datetime | None
    created_at: datetime


class PhotoRead(ApiModel):
    id: uuid.UUID
    place_name: str
    url: str
    thumb_url: str
    width: int
    height: int
    alt: str
    author_name: str
    author_url: str | None
    source: str
    source_url: str


class PlanRequest(ApiModel):
    instructions: str | None = Field(
        default=None,
        max_length=1000,
        description="Extra wishes, e.g. 'one rest day, vegetarian food'",
    )
