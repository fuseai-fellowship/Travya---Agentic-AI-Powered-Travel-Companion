import uuid
from datetime import date, datetime, time
from decimal import Decimal
from enum import StrEnum
from typing import Any

from sqlalchemy import DateTime, Time
from sqlalchemy.dialects.postgresql import JSONB
from sqlmodel import Field

from app.models.base import Table, created_at_field, enum_type, id_field, updated_at_field


class TripStatus(StrEnum):
    draft = "draft"
    planning = "planning"
    planned = "planned"
    booked = "booked"
    completed = "completed"
    cancelled = "cancelled"


class TripPace(StrEnum):
    relaxed = "relaxed"
    balanced = "balanced"
    packed = "packed"


class ItemCategory(StrEnum):
    sight = "sight"
    food = "food"
    activity = "activity"
    transport = "transport"
    lodging = "lodging"
    other = "other"


class BookingKind(StrEnum):
    flight = "flight"
    hotel = "hotel"
    activity = "activity"


class BookingStatus(StrEnum):
    quoted = "quoted"
    confirmed = "confirmed"
    cancelled = "cancelled"


class Trip(Table, table=True):
    __tablename__ = "trips"

    id: uuid.UUID = id_field()
    owner_id: uuid.UUID = Field(foreign_key="users.id", ondelete="CASCADE", index=True)
    title: str = Field(max_length=200)
    destination: str = Field(max_length=200)
    origin: str | None = Field(default=None, max_length=200)
    country_code: str | None = Field(default=None, max_length=2)
    latitude: float | None = None
    longitude: float | None = None
    start_date: date
    end_date: date
    travelers: int = Field(default=1, ge=1, le=20)
    budget: Decimal | None = Field(default=None, max_digits=12, decimal_places=2)
    currency: str = Field(default="USD", min_length=3, max_length=3)
    pace: TripPace = Field(default=TripPace.balanced, sa_type=enum_type(TripPace))
    interests: list[str] = Field(default_factory=list, sa_type=JSONB)
    notes: str | None = Field(default=None, max_length=2000)
    status: TripStatus = Field(default=TripStatus.draft, sa_type=enum_type(TripStatus))
    cover_photo_url: str | None = Field(default=None, max_length=1000)
    plan: dict[str, Any] | None = Field(default=None, sa_type=JSONB)
    planned_at: datetime | None = Field(default=None, sa_type=DateTime(timezone=True))
    # Set while the agents run; a run older than the stale window is treated as dead.
    planning_started_at: datetime | None = Field(default=None, sa_type=DateTime(timezone=True))
    created_at: datetime = created_at_field()
    updated_at: datetime = updated_at_field()


class ItineraryItem(Table, table=True):
    __tablename__ = "itinerary_items"

    id: uuid.UUID = id_field()
    trip_id: uuid.UUID = Field(foreign_key="trips.id", ondelete="CASCADE", index=True)
    day: date
    position: int = 0
    start_time: time | None = Field(default=None, sa_type=Time())
    end_time: time | None = Field(default=None, sa_type=Time())
    title: str = Field(max_length=200)
    description: str | None = Field(default=None, max_length=2000)
    category: ItemCategory = Field(default=ItemCategory.other, sa_type=enum_type(ItemCategory))
    place_name: str | None = Field(default=None, max_length=300)
    latitude: float | None = None
    longitude: float | None = None
    estimated_cost: Decimal | None = Field(default=None, max_digits=12, decimal_places=2)
    source: str = Field(default="user", max_length=16)
    created_at: datetime = created_at_field()
    updated_at: datetime = updated_at_field()


class Booking(Table, table=True):
    """Simulated booking. Quotes come from the planning agents; confirming needs an explicit user action."""

    __tablename__ = "bookings"

    id: uuid.UUID = id_field()
    trip_id: uuid.UUID = Field(foreign_key="trips.id", ondelete="CASCADE", index=True)
    itinerary_item_id: uuid.UUID | None = Field(
        default=None, foreign_key="itinerary_items.id", ondelete="SET NULL", index=True
    )
    kind: BookingKind = Field(sa_type=enum_type(BookingKind))
    title: str = Field(max_length=200)
    provider: str = Field(max_length=120)
    details: dict[str, Any] = Field(default_factory=dict, sa_type=JSONB)
    amount: Decimal = Field(max_digits=12, decimal_places=2)
    currency: str = Field(min_length=3, max_length=3)
    status: BookingStatus = Field(default=BookingStatus.quoted, sa_type=enum_type(BookingStatus))
    confirmation_code: str | None = Field(default=None, max_length=32)
    is_simulated: bool = True
    confirmed_at: datetime | None = Field(default=None, sa_type=DateTime(timezone=True))
    created_at: datetime = created_at_field()
    updated_at: datetime = updated_at_field()


class TripPhoto(Table, table=True):
    __tablename__ = "trip_photos"

    id: uuid.UUID = id_field()
    trip_id: uuid.UUID = Field(foreign_key="trips.id", ondelete="CASCADE", index=True)
    place_name: str = Field(max_length=300)
    position: int = 0
    url: str = Field(max_length=1000)
    thumb_url: str = Field(max_length=1000)
    width: int
    height: int
    alt: str = Field(max_length=500)
    author_name: str = Field(max_length=200)
    author_url: str | None = Field(default=None, max_length=1000)
    source: str = Field(max_length=32)
    source_url: str = Field(max_length=1000)
    created_at: datetime = created_at_field()
