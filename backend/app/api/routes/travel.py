import uuid
from typing import Any, List, Optional
from datetime import date, datetime

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlmodel import func, select

from app.api.deps import CurrentUser, SessionDep
from app.models import (
    Trip, TripCreate, TripUpdate, TripPublic, TripsPublic,
    Itinerary, ItineraryCreate, ItineraryUpdate, ItineraryPublic, ItinerariesPublic,
    Booking, BookingCreate, BookingUpdate, BookingPublic, BookingsPublic,
    TripCollaborator, TripCollaboratorCreate, TripCollaboratorPublic,
    Conversation, ConversationCreate, ConversationPublic,
    ConversationMessage, ConversationMessageCreate, ConversationMessagePublic,
    User, Message
)

router = APIRouter(prefix="/travel", tags=["travel"])


# ===== TRIP ENDPOINTS =====

@router.get("/trips", response_model=TripsPublic)
def read_trips(
    session: SessionDep, 
    current_user: CurrentUser, 
    skip: int = 0, 
    limit: int = 100,
    status: Optional[str] = None,
    trip_type: Optional[str] = None
) -> Any:
    """Retrieve user's trips with optional filtering."""
    
    # Base query for user's trips
    statement = select(Trip).where(Trip.owner_id == current_user.id)
    
    # Apply filters
    if status:
        statement = statement.where(Trip.status == status)
    if trip_type:
        statement = statement.where(Trip.trip_type == trip_type)
    
    # Get count
    count_statement = select(func.count()).select_from(Trip).where(Trip.owner_id == current_user.id)
    if status:
        count_statement = count_statement.where(Trip.status == status)
    if trip_type:
        count_statement = count_statement.where(Trip.trip_type == trip_type)
    
    count = session.exec(count_statement).one()
    trips = session.exec(statement.offset(skip).limit(limit)).all()
    
    return TripsPublic(data=trips, count=count)


@router.get("/trips/{trip_id}", response_model=TripPublic)
def read_trip(session: SessionDep, current_user: CurrentUser, trip_id: uuid.UUID) -> Any:
    """Retrieve a specific trip."""
    
    trip = session.get(Trip, trip_id)
    if not trip:
        raise HTTPException(status_code=404, detail="Trip not found")
    
    # Check if user has access to this trip
    if trip.owner_id != current_user.id:
        # Check if user is a collaborator
        collaborator = session.exec(
            select(TripCollaborator).where(
                TripCollaborator.trip_id == trip_id,
                TripCollaborator.user_id == current_user.id
            )
        ).first()
        if not collaborator:
            raise HTTPException(status_code=403, detail="Not enough permissions")
    
    return trip


@router.post("/trips", response_model=TripPublic)
def create_trip(*, session: SessionDep, current_user: CurrentUser, trip_in: TripCreate) -> Any:
    """Create a new trip."""
    
    trip = Trip.model_validate(trip_in, update={"owner_id": current_user.id})
    session.add(trip)
    session.commit()
    session.refresh(trip)
    return trip


@router.put("/trips/{trip_id}", response_model=TripPublic)
def update_trip(
    *, session: SessionDep, current_user: CurrentUser, trip_id: uuid.UUID, trip_in: TripUpdate
) -> Any:
    """Update a trip."""
    
    trip = session.get(Trip, trip_id)
    if not trip:
        raise HTTPException(status_code=404, detail="Trip not found")
    
    if trip.owner_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not enough permissions")
    
    trip_dict = trip_in.model_dump(exclude_unset=True)
    for field, value in trip_dict.items():
        setattr(trip, field, value)
    
    trip.updated_at = datetime.utcnow()
    session.add(trip)
    session.commit()
    session.refresh(trip)
    return trip


@router.delete("/trips/{trip_id}")
def delete_trip(session: SessionDep, current_user: CurrentUser, trip_id: uuid.UUID) -> Message:
    """Delete a trip."""
    
    trip = session.get(Trip, trip_id)
    if not trip:
        raise HTTPException(status_code=404, detail="Trip not found")
    
    if trip.owner_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not enough permissions")
    
    session.delete(trip)
    session.commit()
    return Message(message="Trip deleted successfully")


# ===== ITINERARY ENDPOINTS =====

@router.get("/trips/{trip_id}/itineraries", response_model=ItinerariesPublic)
def read_itineraries(
    session: SessionDep, 
    current_user: CurrentUser, 
    trip_id: uuid.UUID,
    skip: int = 0, 
    limit: int = 100
) -> Any:
    """Retrieve itineraries for a trip."""
    
    # Check trip access
    trip = session.get(Trip, trip_id)
    if not trip:
        raise HTTPException(status_code=404, detail="Trip not found")
    
    if trip.owner_id != current_user.id:
        collaborator = session.exec(
            select(TripCollaborator).where(
                TripCollaborator.trip_id == trip_id,
                TripCollaborator.user_id == current_user.id
            )
        ).first()
        if not collaborator:
            raise HTTPException(status_code=403, detail="Not enough permissions")
    
    # Get itineraries
    count_statement = select(func.count()).select_from(Itinerary).where(Itinerary.trip_id == trip_id)
    count = session.exec(count_statement).one()
    
    statement = (
        select(Itinerary)
        .where(Itinerary.trip_id == trip_id)
        .order_by(Itinerary.date, Itinerary.order_index)
        .offset(skip)
        .limit(limit)
    )
    itineraries = session.exec(statement).all()
    
    return ItinerariesPublic(data=itineraries, count=count)


@router.post("/trips/{trip_id}/itineraries", response_model=ItineraryPublic)
def create_itinerary(
    *, session: SessionDep, current_user: CurrentUser, trip_id: uuid.UUID, itinerary_in: ItineraryCreate
) -> Any:
    """Create a new itinerary item."""
    
    # Check trip access
    trip = session.get(Trip, trip_id)
    if not trip:
        raise HTTPException(status_code=404, detail="Trip not found")
    
    if trip.owner_id != current_user.id:
        collaborator = session.exec(
            select(TripCollaborator).where(
                TripCollaborator.trip_id == trip_id,
                TripCollaborator.user_id == current_user.id,
                TripCollaborator.permission.in_(["edit", "admin"])
            )
        ).first()
        if not collaborator:
            raise HTTPException(status_code=403, detail="Not enough permissions")
    
    # Create itinerary
    itinerary_dict = itinerary_in.model_dump()
    itinerary_dict["trip_id"] = trip_id
    itinerary = Itinerary.model_validate(itinerary_dict)
    
    session.add(itinerary)
    session.commit()
    session.refresh(itinerary)
    return itinerary


@router.put("/itineraries/{itinerary_id}", response_model=ItineraryPublic)
def update_itinerary(
    *, session: SessionDep, current_user: CurrentUser, itinerary_id: uuid.UUID, itinerary_in: ItineraryUpdate
) -> Any:
    """Update an itinerary item."""
    
    itinerary = session.get(Itinerary, itinerary_id)
    if not itinerary:
        raise HTTPException(status_code=404, detail="Itinerary not found")
    
    # Check trip access
    trip = session.get(Trip, itinerary.trip_id)
    if trip.owner_id != current_user.id:
        collaborator = session.exec(
            select(TripCollaborator).where(
                TripCollaborator.trip_id == itinerary.trip_id,
                TripCollaborator.user_id == current_user.id,
                TripCollaborator.permission.in_(["edit", "admin"])
            )
        ).first()
        if not collaborator:
            raise HTTPException(status_code=403, detail="Not enough permissions")
    
    itinerary_dict = itinerary_in.model_dump(exclude_unset=True)
    for field, value in itinerary_dict.items():
        setattr(itinerary, field, value)
    
    itinerary.updated_at = datetime.utcnow()
    session.add(itinerary)
    session.commit()
    session.refresh(itinerary)
    return itinerary


@router.delete("/itineraries/{itinerary_id}")
def delete_itinerary(session: SessionDep, current_user: CurrentUser, itinerary_id: uuid.UUID) -> Message:
    """Delete an itinerary item."""
    
    itinerary = session.get(Itinerary, itinerary_id)
    if not itinerary:
        raise HTTPException(status_code=404, detail="Itinerary not found")
    
    # Check trip access
    trip = session.get(Trip, itinerary.trip_id)
    if trip.owner_id != current_user.id:
        collaborator = session.exec(
            select(TripCollaborator).where(
                TripCollaborator.trip_id == itinerary.trip_id,
                TripCollaborator.user_id == current_user.id,
                TripCollaborator.permission.in_(["edit", "admin"])
            )
        ).first()
        if not collaborator:
            raise HTTPException(status_code=403, detail="Not enough permissions")
    
    session.delete(itinerary)
    session.commit()
    return Message(message="Itinerary deleted successfully")


# ===== BOOKING ENDPOINTS =====

@router.get("/trips/{trip_id}/bookings", response_model=BookingsPublic)
def read_bookings(
    session: SessionDep, 
    current_user: CurrentUser, 
    trip_id: uuid.UUID,
    skip: int = 0, 
    limit: int = 100
) -> Any:
    """Retrieve bookings for a trip."""
    
    # Check trip access
    trip = session.get(Trip, trip_id)
    if not trip:
        raise HTTPException(status_code=404, detail="Trip not found")
    
    if trip.owner_id != current_user.id:
        collaborator = session.exec(
            select(TripCollaborator).where(
                TripCollaborator.trip_id == trip_id,
                TripCollaborator.user_id == current_user.id
            )
        ).first()
        if not collaborator:
            raise HTTPException(status_code=403, detail="Not enough permissions")
    
    # Get bookings
    count_statement = select(func.count()).select_from(Booking).where(Booking.trip_id == trip_id)
    count = session.exec(count_statement).one()
    
    statement = (
        select(Booking)
        .where(Booking.trip_id == trip_id)
        .order_by(Booking.created_at.desc())
        .offset(skip)
        .limit(limit)
    )
    bookings = session.exec(statement).all()
    
    return BookingsPublic(data=bookings, count=count)


@router.post("/trips/{trip_id}/bookings", response_model=BookingPublic)
def create_booking(
    *, session: SessionDep, current_user: CurrentUser, trip_id: uuid.UUID, booking_in: BookingCreate
) -> Any:
    """Create a new booking."""
    
    # Check trip access
    trip = session.get(Trip, trip_id)
    if not trip:
        raise HTTPException(status_code=404, detail="Trip not found")
    
    if trip.owner_id != current_user.id:
        collaborator = session.exec(
            select(TripCollaborator).where(
                TripCollaborator.trip_id == trip_id,
                TripCollaborator.user_id == current_user.id,
                TripCollaborator.permission.in_(["edit", "admin"])
            )
        ).first()
        if not collaborator:
            raise HTTPException(status_code=403, detail="Not enough permissions")
    
    # Create booking
    booking_dict = booking_in.model_dump()
    booking_dict["trip_id"] = trip_id
    booking = Booking.model_validate(booking_dict)
    
    session.add(booking)
    session.commit()
    session.refresh(booking)
    return booking


@router.put("/bookings/{booking_id}", response_model=BookingPublic)
def update_booking(
    *, session: SessionDep, current_user: CurrentUser, booking_id: uuid.UUID, booking_in: BookingUpdate
) -> Any:
    """Update a booking."""
    
    booking = session.get(Booking, booking_id)
    if not booking:
        raise HTTPException(status_code=404, detail="Booking not found")
    
    # Check trip access
    trip = session.get(Trip, booking.trip_id)
    if trip.owner_id != current_user.id:
        collaborator = session.exec(
            select(TripCollaborator).where(
                TripCollaborator.trip_id == booking.trip_id,
                TripCollaborator.user_id == current_user.id,
                TripCollaborator.permission.in_(["edit", "admin"])
            )
        ).first()
        if not collaborator:
            raise HTTPException(status_code=403, detail="Not enough permissions")
    
    booking_dict = booking_in.model_dump(exclude_unset=True)
    for field, value in booking_dict.items():
        setattr(booking, field, value)
    
    booking.updated_at = datetime.utcnow()
    session.add(booking)
    session.commit()
    session.refresh(booking)
    return booking


@router.delete("/bookings/{booking_id}")
def delete_booking(session: SessionDep, current_user: CurrentUser, booking_id: uuid.UUID) -> Message:
    """Delete a booking."""
    
    booking = session.get(Booking, booking_id)
    if not booking:
        raise HTTPException(status_code=404, detail="Booking not found")
    
    # Check trip access
    trip = session.get(Trip, booking.trip_id)
    if trip.owner_id != current_user.id:
        collaborator = session.exec(
            select(TripCollaborator).where(
                TripCollaborator.trip_id == booking.trip_id,
                TripCollaborator.user_id == current_user.id,
                TripCollaborator.permission.in_(["edit", "admin"])
            )
        ).first()
        if not collaborator:
            raise HTTPException(status_code=403, detail="Not enough permissions")
    
    session.delete(booking)
    session.commit()
    return Message(message="Booking deleted successfully")


# ===== COLLABORATION ENDPOINTS =====

@router.get("/trips/{trip_id}/collaborators")
def read_collaborators(session: SessionDep, current_user: CurrentUser, trip_id: uuid.UUID) -> Any:
    """Retrieve collaborators for a trip."""
    
    # Check trip access
    trip = session.get(Trip, trip_id)
    if not trip:
        raise HTTPException(status_code=404, detail="Trip not found")
    
    if trip.owner_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not enough permissions")
    
    # Get collaborators
    statement = (
        select(TripCollaborator, User)
        .join(User, TripCollaborator.user_id == User.id)
        .where(TripCollaborator.trip_id == trip_id)
    )
    results = session.exec(statement).all()
    
    collaborators = []
    for collaborator, user in results:
        collaborators.append({
            "id": collaborator.id,
            "user_id": collaborator.user_id,
            "user_email": user.email,
            "user_name": user.full_name,
            "permission": collaborator.permission,
            "created_at": collaborator.created_at
        })
    
    return {"collaborators": collaborators}


@router.post("/trips/{trip_id}/collaborators")
def add_collaborator(
    *, session: SessionDep, current_user: CurrentUser, trip_id: uuid.UUID, collaborator_in: TripCollaboratorCreate
) -> Any:
    """Add a collaborator to a trip."""
    
    # Check trip access
    trip = session.get(Trip, trip_id)
    if not trip:
        raise HTTPException(status_code=404, detail="Trip not found")
    
    if trip.owner_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not enough permissions")
    
    # Find user by email
    user = session.exec(select(User).where(User.email == collaborator_in.user_email)).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    # Check if already a collaborator
    existing = session.exec(
        select(TripCollaborator).where(
            TripCollaborator.trip_id == trip_id,
            TripCollaborator.user_id == user.id
        )
    ).first()
    if existing:
        raise HTTPException(status_code=400, detail="User is already a collaborator")
    
    # Create collaborator
    collaborator = TripCollaborator(
        trip_id=trip_id,
        user_id=user.id,
        invited_by=current_user.id,
        permission=collaborator_in.permission
    )
    
    session.add(collaborator)
    session.commit()
    session.refresh(collaborator)
    
    return {
        "message": "Collaborator added successfully",
        "collaborator": {
            "id": collaborator.id,
            "user_email": user.email,
            "user_name": user.full_name,
            "permission": collaborator.permission
        }
    }


@router.delete("/trips/{trip_id}/collaborators/{collaborator_id}")
def remove_collaborator(
    session: SessionDep, current_user: CurrentUser, trip_id: uuid.UUID, collaborator_id: uuid.UUID
) -> Message:
    """Remove a collaborator from a trip."""
    
    # Check trip access
    trip = session.get(Trip, trip_id)
    if not trip:
        raise HTTPException(status_code=404, detail="Trip not found")
    
    if trip.owner_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not enough permissions")
    
    # Find collaborator
    collaborator = session.get(TripCollaborator, collaborator_id)
    if not collaborator or collaborator.trip_id != trip_id:
        raise HTTPException(status_code=404, detail="Collaborator not found")
    
    session.delete(collaborator)
    session.commit()
    return Message(message="Collaborator removed successfully")


# ===== CONVERSATION ENDPOINTS =====

@router.get("/conversations")
def read_conversations(
    session: SessionDep, 
    current_user: CurrentUser, 
    skip: int = 0, 
    limit: int = 100
) -> Any:
    """Retrieve user's conversations."""
    
    count_statement = select(func.count()).select_from(Conversation).where(Conversation.user_id == current_user.id)
    count = session.exec(count_statement).one()
    
    statement = (
        select(Conversation)
        .where(Conversation.user_id == current_user.id)
        .order_by(Conversation.updated_at.desc())
        .offset(skip)
        .limit(limit)
    )
    conversations = session.exec(statement).all()
    
    return {"conversations": conversations, "count": count}


@router.post("/conversations", response_model=ConversationPublic)
def create_conversation(
    *, session: SessionDep, current_user: CurrentUser, conversation_in: ConversationCreate
) -> Any:
    """Create a new conversation."""
    
    conversation_dict = conversation_in.model_dump()
    conversation_dict["user_id"] = current_user.id
    conversation = Conversation.model_validate(conversation_dict)
    
    session.add(conversation)
    session.commit()
    session.refresh(conversation)
    return conversation


@router.get("/conversations/{conversation_id}/messages")
def read_messages(
    session: SessionDep, 
    current_user: CurrentUser, 
    conversation_id: uuid.UUID,
    skip: int = 0, 
    limit: int = 100
) -> Any:
    """Retrieve messages for a conversation."""
    
    # Check conversation access
    conversation = session.get(Conversation, conversation_id)
    if not conversation:
        raise HTTPException(status_code=404, detail="Conversation not found")
    
    if conversation.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not enough permissions")
    
    # Get messages
    count_statement = select(func.count()).select_from(ConversationMessage).where(
        ConversationMessage.conversation_id == conversation_id
    )
    count = session.exec(count_statement).one()
    
    statement = (
        select(ConversationMessage)
        .where(ConversationMessage.conversation_id == conversation_id)
        .order_by(ConversationMessage.created_at.asc())
        .offset(skip)
        .limit(limit)
    )
    messages = session.exec(statement).all()
    
    return {"messages": messages, "count": count}


@router.post("/conversations/{conversation_id}/messages", response_model=ConversationMessagePublic)
def create_message(
    *, session: SessionDep, current_user: CurrentUser, conversation_id: uuid.UUID, message_in: ConversationMessageCreate
) -> Any:
    """Create a new message in a conversation."""
    
    # Check conversation access
    conversation = session.get(Conversation, conversation_id)
    if not conversation:
        raise HTTPException(status_code=404, detail="Conversation not found")
    
    if conversation.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not enough permissions")
    
    # Create message
    message_dict = message_in.model_dump()
    message_dict["conversation_id"] = conversation_id
    message = ConversationMessage.model_validate(message_dict)
    
    session.add(message)
    
    # Update conversation timestamp
    conversation.updated_at = datetime.utcnow()
    session.add(conversation)
    
    session.commit()
    session.refresh(message)
    return message


@router.delete("/conversations/{conversation_id}")
def delete_conversation(
    session: SessionDep,
    current_user: CurrentUser,
    conversation_id: uuid.UUID
) -> Message:
    """Delete a conversation and all its messages."""
    
    conversation = session.get(Conversation, conversation_id)
    if not conversation:
        raise HTTPException(status_code=404, detail="Conversation not found")
    
    if conversation.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not enough permissions")
    
    session.delete(conversation)
    session.commit()
    return Message(message="Conversation deleted successfully")
