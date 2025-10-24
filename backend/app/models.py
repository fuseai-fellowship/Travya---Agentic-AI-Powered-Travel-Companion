#backend/app/models.py
import uuid
from datetime import datetime, date
from typing import Optional, List
from enum import Enum

from pydantic import EmailStr
from sqlmodel import Field, Relationship, SQLModel


# Shared properties
class UserBase(SQLModel):
    email: EmailStr = Field(unique=True, index=True, max_length=255)
    is_active: bool = True
    is_superuser: bool = False
    full_name: str | None = Field(default=None, max_length=255)


# Properties to receive via API on creation
class UserCreate(UserBase):
    password: str = Field(min_length=8, max_length=40)


class UserRegister(SQLModel):
    email: EmailStr = Field(max_length=255)
    password: str = Field(min_length=8, max_length=40)
    full_name: str | None = Field(default=None, max_length=255)


# Properties to receive via API on update, all are optional
class UserUpdate(UserBase):
    email: EmailStr | None = Field(default=None, max_length=255)  # type: ignore
    password: str | None = Field(default=None, min_length=8, max_length=40)


class UserUpdateMe(SQLModel):
    full_name: str | None = Field(default=None, max_length=255)
    email: EmailStr | None = Field(default=None, max_length=255)


class UpdatePassword(SQLModel):
    current_password: str = Field(min_length=8, max_length=40)
    new_password: str = Field(min_length=8, max_length=40)


# Database model, database table inferred from class name
class User(UserBase, table=True):
    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    hashed_password: str
    items: list["Item"] = Relationship(back_populates="owner", cascade_delete=True)
    trips: List["Trip"] = Relationship(back_populates="owner", cascade_delete=True)
    conversations: List["Conversation"] = Relationship(back_populates="user", cascade_delete=True)


# Properties to return via API, id is always required
class UserPublic(UserBase):
    id: uuid.UUID


class UsersPublic(SQLModel):
    data: list[UserPublic]
    count: int


# Shared properties
class ItemBase(SQLModel):
    title: str = Field(min_length=1, max_length=255)
    description: str | None = Field(default=None, max_length=255)


# Properties to receive on item creation
class ItemCreate(ItemBase):
    pass


# Properties to receive on item update
class ItemUpdate(ItemBase):
    title: str | None = Field(default=None, min_length=1, max_length=255)  # type: ignore


# Database model, database table inferred from class name
class Item(ItemBase, table=True):
    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    owner_id: uuid.UUID = Field(
        foreign_key="user.id", nullable=False, ondelete="CASCADE"
    )
    owner: User | None = Relationship(back_populates="items")


# Properties to return via API, id is always required
class ItemPublic(ItemBase):
    id: uuid.UUID
    owner_id: uuid.UUID


class ItemsPublic(SQLModel):
    data: list[ItemPublic]
    count: int


# Generic message
class Message(SQLModel):
    message: str


# JSON payload containing access token
class Token(SQLModel):
    access_token: str
    token_type: str = "bearer"


# Contents of JWT token
class TokenPayload(SQLModel):
    sub: str | None = None


class NewPassword(SQLModel):
    token: str
    new_password: str = Field(min_length=8, max_length=40)


# ===== TRAVEL MODELS =====

class TripStatus(str, Enum):
    DRAFT = "draft"
    PLANNING = "planning"
    CONFIRMED = "confirmed"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    CANCELLED = "cancelled"


class BookingStatus(str, Enum):
    PENDING = "pending"
    CONFIRMED = "confirmed"
    CANCELLED = "cancelled"
    COMPLETED = "completed"


class TripType(str, Enum):
    LEISURE = "leisure"
    BUSINESS = "business"
    ADVENTURE = "adventure"
    CULTURAL = "cultural"
    ROMANTIC = "romantic"
    FAMILY = "family"
    SOLO = "solo"


# Trip Models
class TripBase(SQLModel):
    title: str = Field(min_length=1, max_length=255)
    description: Optional[str] = Field(default=None, max_length=1000)
    destination: str = Field(min_length=1, max_length=255)
    start_date: date
    end_date: date
    budget: Optional[float] = Field(default=None, ge=0)
    trip_type: TripType = Field(default=TripType.LEISURE)
    status: TripStatus = Field(default=TripStatus.DRAFT)
    is_public: bool = Field(default=False)
    cover_image_url: Optional[str] = Field(default=None, max_length=500)
    ai_itinerary_data: Optional[str] = Field(default=None)  # JSON string of AI-generated itinerary


class TripCreate(TripBase):
    pass


class TripUpdate(SQLModel):
    title: Optional[str] = Field(default=None, min_length=1, max_length=255)
    description: Optional[str] = Field(default=None, max_length=1000)
    destination: Optional[str] = Field(default=None, min_length=1, max_length=255)
    start_date: Optional[date] = None
    end_date: Optional[date] = None
    budget: Optional[float] = Field(default=None, ge=0)
    trip_type: Optional[TripType] = None
    status: Optional[TripStatus] = None
    is_public: Optional[bool] = None
    cover_image_url: Optional[str] = Field(default=None, max_length=500)
    ai_itinerary_data: Optional[str] = Field(default=None)


class Trip(TripBase, table=True):
    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    owner_id: uuid.UUID = Field(foreign_key="user.id", nullable=False, ondelete="CASCADE")
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    
    # Relationships
    owner: User = Relationship(back_populates="trips")
    itineraries: List["Itinerary"] = Relationship(back_populates="trip", cascade_delete=True)
    bookings: List["Booking"] = Relationship(back_populates="trip", cascade_delete=True)
    collaborators: List["TripCollaborator"] = Relationship(back_populates="trip", cascade_delete=True)


class TripPublic(TripBase):
    id: uuid.UUID
    owner_id: uuid.UUID
    created_at: datetime
    updated_at: datetime
    ai_itinerary_data: Optional[str] = None


class TripsPublic(SQLModel):
    data: List[TripPublic]
    count: int


# Itinerary Models
class ItineraryBase(SQLModel):
    title: str = Field(min_length=1, max_length=255)
    description: Optional[str] = Field(default=None, max_length=1000)
    date: date
    start_time: Optional[str] = Field(default=None, max_length=10)  # HH:MM format
    end_time: Optional[str] = Field(default=None, max_length=10)    # HH:MM format
    location: str = Field(min_length=1, max_length=255)
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    estimated_cost: Optional[float] = Field(default=None, ge=0)
    notes: Optional[str] = Field(default=None, max_length=2000)
    image_urls: Optional[str] = Field(default=None, max_length=2000)  # JSON string of URLs


class ItineraryCreate(ItineraryBase):
    trip_id: uuid.UUID


class ItineraryUpdate(SQLModel):
    title: Optional[str] = Field(default=None, min_length=1, max_length=255)
    description: Optional[str] = Field(default=None, max_length=1000)
    date: Optional[date] = None
    start_time: Optional[str] = Field(default=None, max_length=10)
    end_time: Optional[str] = Field(default=None, max_length=10)
    location: Optional[str] = Field(default=None, min_length=1, max_length=255)
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    estimated_cost: Optional[float] = Field(default=None, ge=0)
    notes: Optional[str] = Field(default=None, max_length=2000)
    image_urls: Optional[str] = Field(default=None, max_length=2000)


class Itinerary(ItineraryBase, table=True):
    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    trip_id: uuid.UUID = Field(foreign_key="trip.id", nullable=False, ondelete="CASCADE")
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    order_index: int = Field(default=0)
    
    # Relationships
    trip: Trip = Relationship(back_populates="itineraries")
    bookings: List["Booking"] = Relationship(back_populates="itinerary", cascade_delete=True)


class ItineraryPublic(ItineraryBase):
    id: uuid.UUID
    trip_id: uuid.UUID
    created_at: datetime
    updated_at: datetime
    order_index: int


class ItinerariesPublic(SQLModel):
    data: List[ItineraryPublic]
    count: int


# Booking Models
class BookingBase(SQLModel):
    title: str = Field(min_length=1, max_length=255)
    booking_type: str = Field(min_length=1, max_length=50)  # flight, hotel, restaurant, activity, etc.
    provider: str = Field(min_length=1, max_length=255)     # airline, hotel chain, etc.
    confirmation_number: Optional[str] = Field(default=None, max_length=100)
    booking_date: Optional[date] = None
    check_in_date: Optional[date] = None
    check_out_date: Optional[date] = None
    amount: Optional[float] = Field(default=None, ge=0)
    currency: str = Field(default="USD", max_length=3)
    status: BookingStatus = Field(default=BookingStatus.PENDING)
    notes: Optional[str] = Field(default=None, max_length=2000)
    document_urls: Optional[str] = Field(default=None, max_length=2000)  # JSON string of URLs


class BookingCreate(BookingBase):
    trip_id: uuid.UUID
    itinerary_id: Optional[uuid.UUID] = None


class BookingUpdate(SQLModel):
    title: Optional[str] = Field(default=None, min_length=1, max_length=255)
    booking_type: Optional[str] = Field(default=None, min_length=1, max_length=50)
    provider: Optional[str] = Field(default=None, min_length=1, max_length=255)
    confirmation_number: Optional[str] = Field(default=None, max_length=100)
    booking_date: Optional[date] = None
    check_in_date: Optional[date] = None
    check_out_date: Optional[date] = None
    amount: Optional[float] = Field(default=None, ge=0)
    currency: Optional[str] = Field(default=None, max_length=3)
    status: Optional[BookingStatus] = None
    notes: Optional[str] = Field(default=None, max_length=2000)
    document_urls: Optional[str] = Field(default=None, max_length=2000)


class Booking(BookingBase, table=True):
    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    trip_id: uuid.UUID = Field(foreign_key="trip.id", nullable=False, ondelete="CASCADE")
    itinerary_id: Optional[uuid.UUID] = Field(foreign_key="itinerary.id", nullable=True, ondelete="SET NULL")
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    
    # Relationships
    trip: Trip = Relationship(back_populates="bookings")
    itinerary: Optional[Itinerary] = Relationship(back_populates="bookings")


class BookingPublic(BookingBase):
    id: uuid.UUID
    trip_id: uuid.UUID
    itinerary_id: Optional[uuid.UUID]
    created_at: datetime
    updated_at: datetime


class BookingsPublic(SQLModel):
    data: List[BookingPublic]
    count: int


# Collaboration Models
class TripCollaboratorBase(SQLModel):
    permission: str = Field(default="view", max_length=20)  # view, edit, admin


class TripCollaboratorCreate(TripCollaboratorBase):
    trip_id: uuid.UUID
    user_email: EmailStr


class TripCollaborator(TripCollaboratorBase, table=True):
    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    trip_id: uuid.UUID = Field(foreign_key="trip.id", nullable=False, ondelete="CASCADE")
    user_id: uuid.UUID = Field(foreign_key="user.id", nullable=False, ondelete="CASCADE")
    invited_by: uuid.UUID = Field(foreign_key="user.id", nullable=False)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    
    # Relationships
    trip: Trip = Relationship(back_populates="collaborators")
    user: User = Relationship(sa_relationship_kwargs={"foreign_keys": "[TripCollaborator.user_id]"})
    inviter: User = Relationship(sa_relationship_kwargs={"foreign_keys": "[TripCollaborator.invited_by]"})


class TripCollaboratorPublic(TripCollaboratorBase):
    id: uuid.UUID
    trip_id: uuid.UUID
    user_id: uuid.UUID
    invited_by: uuid.UUID
    created_at: datetime


# Chat/Conversation Models
class ConversationBase(SQLModel):
    title: Optional[str] = Field(default=None, max_length=255)
    trip_id: Optional[uuid.UUID] = None


class ConversationCreate(ConversationBase):
    pass


class ConversationUpdate(SQLModel):
    title: Optional[str] = Field(default=None, max_length=255)
    trip_id: Optional[uuid.UUID] = None


class Conversation(ConversationBase, table=True):
    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    user_id: uuid.UUID = Field(foreign_key="user.id", nullable=False, ondelete="CASCADE")
    last_message: Optional[str] = Field(default=None, max_length=100)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    
    # Relationships
    user: User = Relationship(back_populates="conversations")
    messages: List["ConversationMessage"] = Relationship(back_populates="conversation", cascade_delete=True)


class ConversationPublic(ConversationBase):
    id: uuid.UUID
    user_id: uuid.UUID
    last_message: Optional[str]
    created_at: datetime
    updated_at: datetime


class ConversationMessageBase(SQLModel):
    content: str = Field(min_length=1, max_length=10000)
    sender: str = Field(max_length=20)  # user, ai, system


class ConversationMessageCreate(ConversationMessageBase):
    conversation_id: uuid.UUID


class ConversationMessage(ConversationMessageBase, table=True):
    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    conversation_id: uuid.UUID = Field(foreign_key="conversation.id", nullable=False, ondelete="CASCADE")
    created_at: datetime = Field(default_factory=datetime.utcnow)
    
    # Relationships
    conversation: Conversation = Relationship(back_populates="messages")


class ConversationMessagePublic(ConversationMessageBase):
    id: uuid.UUID
    conversation_id: uuid.UUID
    created_at: datetime


class ConversationsPublic(SQLModel):
    data: List[ConversationPublic]
    count: int


class ConversationMessagesPublic(SQLModel):
    data: List[ConversationMessagePublic]
    count: int


