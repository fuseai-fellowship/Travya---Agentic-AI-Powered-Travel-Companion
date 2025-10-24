#backend/app/crud.py
import uuid
from typing import Any, List, Optional
from datetime import datetime

from sqlmodel import Session, select, func

from app.core.security import get_password_hash, verify_password
from app.models import (
    Item, ItemCreate, User, UserCreate, UserUpdate,
    Trip, TripCreate, TripUpdate,
    Conversation, ConversationCreate, ConversationUpdate,
    ConversationMessage, ConversationMessageCreate,
    Itinerary, ItineraryCreate, ItineraryUpdate,
    Booking, BookingCreate, BookingUpdate
)


def create_user(*, session: Session, user_create: UserCreate) -> User:
    db_obj = User.model_validate(
        user_create, update={"hashed_password": get_password_hash(user_create.password)}
    )
    session.add(db_obj)
    session.commit()
    session.refresh(db_obj)
    return db_obj


def update_user(*, session: Session, db_user: User, user_in: UserUpdate) -> Any:
    user_data = user_in.model_dump(exclude_unset=True)
    extra_data = {}
    if "password" in user_data:
        password = user_data["password"]
        hashed_password = get_password_hash(password)
        extra_data["hashed_password"] = hashed_password
    db_user.sqlmodel_update(user_data, update=extra_data)
    session.add(db_user)
    session.commit()
    session.refresh(db_user)
    return db_user


def get_user_by_email(*, session: Session, email: str) -> User | None:
    statement = select(User).where(User.email == email)
    session_user = session.exec(statement).first()
    return session_user


def authenticate(*, session: Session, email: str, password: str) -> User | None:
    db_user = get_user_by_email(session=session, email=email)
    if not db_user:
        return None
    if not verify_password(password, db_user.hashed_password):
        return None
    return db_user


def create_item(*, session: Session, item_in: ItemCreate, owner_id: uuid.UUID) -> Item:
    db_item = Item.model_validate(item_in, update={"owner_id": owner_id})
    session.add(db_item)
    session.commit()
    session.refresh(db_item)
    return db_item


# ===== TRIP CRUD OPERATIONS =====

def create_trip(*, session: Session, trip_in: TripCreate, owner_id: uuid.UUID) -> Trip:
    """Create a new trip."""
    trip = Trip.model_validate(trip_in, update={"owner_id": owner_id})
    session.add(trip)
    session.commit()
    session.refresh(trip)
    return trip


def get_trip(*, session: Session, trip_id: uuid.UUID) -> Optional[Trip]:
    """Get a trip by ID."""
    return session.get(Trip, trip_id)


def get_user_trips(*, session: Session, user_id: uuid.UUID, skip: int = 0, limit: int = 100) -> List[Trip]:
    """Get trips for a user."""
    statement = select(Trip).where(Trip.owner_id == user_id).offset(skip).limit(limit)
    return session.exec(statement).all()


def update_trip(*, session: Session, trip: Trip, trip_in: TripUpdate) -> Trip:
    """Update a trip."""
    trip_dict = trip_in.model_dump(exclude_unset=True)
    for field, value in trip_dict.items():
        setattr(trip, field, value)
    
    trip.updated_at = datetime.utcnow()
    session.add(trip)
    session.commit()
    session.refresh(trip)
    return trip


def delete_trip(*, session: Session, trip: Trip) -> None:
    """Delete a trip."""
    session.delete(trip)
    session.commit()


# ===== CONVERSATION CRUD OPERATIONS =====

def create_conversation(*, session: Session, conversation_in: ConversationCreate, user_id: uuid.UUID) -> Conversation:
    """Create a new conversation."""
    conversation = Conversation.model_validate(conversation_in, update={"user_id": user_id})
    session.add(conversation)
    session.commit()
    session.refresh(conversation)
    return conversation


def get_conversation(*, session: Session, conversation_id: uuid.UUID) -> Optional[Conversation]:
    """Get a conversation by ID."""
    return session.get(Conversation, conversation_id)


def get_user_conversations(*, session: Session, user_id: uuid.UUID, skip: int = 0, limit: int = 100) -> List[Conversation]:
    """Get conversations for a user."""
    statement = (
        select(Conversation)
        .where(Conversation.user_id == user_id)
        .order_by(Conversation.updated_at.desc())
        .offset(skip)
        .limit(limit)
    )
    return session.exec(statement).all()


def update_conversation(*, session: Session, conversation: Conversation, conversation_in: ConversationUpdate) -> Conversation:
    """Update a conversation."""
    conversation_dict = conversation_in.model_dump(exclude_unset=True)
    for field, value in conversation_dict.items():
        setattr(conversation, field, value)
    
    conversation.updated_at = datetime.utcnow()
    session.add(conversation)
    session.commit()
    session.refresh(conversation)
    return conversation


def delete_conversation(*, session: Session, conversation: Conversation) -> None:
    """Delete a conversation."""
    session.delete(conversation)
    session.commit()


# ===== CONVERSATION MESSAGE CRUD OPERATIONS =====

def create_conversation_message(*, session: Session, message_in: ConversationMessageCreate) -> ConversationMessage:
    """Create a new conversation message."""
    message = ConversationMessage.model_validate(message_in)
    session.add(message)
    session.commit()
    session.refresh(message)
    return message


def get_conversation_messages(*, session: Session, conversation_id: uuid.UUID, skip: int = 0, limit: int = 100) -> List[ConversationMessage]:
    """Get messages for a conversation."""
    statement = (
        select(ConversationMessage)
        .where(ConversationMessage.conversation_id == conversation_id)
        .order_by(ConversationMessage.created_at.asc())
        .offset(skip)
        .limit(limit)
    )
    return session.exec(statement).all()


# ===== ITINERARY CRUD OPERATIONS =====

def create_itinerary(*, session: Session, itinerary_in: ItineraryCreate) -> Itinerary:
    """Create a new itinerary item."""
    itinerary = Itinerary.model_validate(itinerary_in)
    session.add(itinerary)
    session.commit()
    session.refresh(itinerary)
    return itinerary


def get_itinerary(*, session: Session, itinerary_id: uuid.UUID) -> Optional[Itinerary]:
    """Get an itinerary by ID."""
    return session.get(Itinerary, itinerary_id)


def get_trip_itineraries(*, session: Session, trip_id: uuid.UUID, skip: int = 0, limit: int = 100) -> List[Itinerary]:
    """Get itineraries for a trip."""
    statement = (
        select(Itinerary)
        .where(Itinerary.trip_id == trip_id)
        .order_by(Itinerary.date, Itinerary.order_index)
        .offset(skip)
        .limit(limit)
    )
    return session.exec(statement).all()


def update_itinerary(*, session: Session, itinerary: Itinerary, itinerary_in: ItineraryUpdate) -> Itinerary:
    """Update an itinerary."""
    itinerary_dict = itinerary_in.model_dump(exclude_unset=True)
    for field, value in itinerary_dict.items():
        setattr(itinerary, field, value)
    
    itinerary.updated_at = datetime.utcnow()
    session.add(itinerary)
    session.commit()
    session.refresh(itinerary)
    return itinerary


def delete_itinerary(*, session: Session, itinerary: Itinerary) -> None:
    """Delete an itinerary."""
    session.delete(itinerary)
    session.commit()


# ===== BOOKING CRUD OPERATIONS =====

def create_booking(*, session: Session, booking_in: BookingCreate) -> Booking:
    """Create a new booking."""
    booking = Booking.model_validate(booking_in)
    session.add(booking)
    session.commit()
    session.refresh(booking)
    return booking


def get_booking(*, session: Session, booking_id: uuid.UUID) -> Optional[Booking]:
    """Get a booking by ID."""
    return session.get(Booking, booking_id)


def get_trip_bookings(*, session: Session, trip_id: uuid.UUID, skip: int = 0, limit: int = 100) -> List[Booking]:
    """Get bookings for a trip."""
    statement = (
        select(Booking)
        .where(Booking.trip_id == trip_id)
        .order_by(Booking.created_at.desc())
        .offset(skip)
        .limit(limit)
    )
    return session.exec(statement).all()


def update_booking(*, session: Session, booking: Booking, booking_in: BookingUpdate) -> Booking:
    """Update a booking."""
    booking_dict = booking_in.model_dump(exclude_unset=True)
    for field, value in booking_dict.items():
        setattr(booking, field, value)
    
    booking.updated_at = datetime.utcnow()
    session.add(booking)
    session.commit()
    session.refresh(booking)
    return booking


def delete_booking(*, session: Session, booking: Booking) -> None:
    """Delete a booking."""
    session.delete(booking)
    session.commit()
