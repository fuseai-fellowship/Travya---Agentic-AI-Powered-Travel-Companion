from typing import ClassVar

from app.models import (
    Booking,
    Conversation,
    Document,
    Feedback,
    ItineraryItem,
    Message,
    Note,
    Trip,
    TripPhoto,
)
from app.repositories.base import ScopedRepository, newest_first


class TripRepository(ScopedRepository[Trip]):
    model = Trip
    scope_column = "owner_id"
    not_found: ClassVar[str] = "Trip not found"


class ItineraryRepository(ScopedRepository[ItineraryItem]):
    """Scoped to a trip that was loaded through TripRepository."""

    model = ItineraryItem
    scope_column = "trip_id"
    not_found: ClassVar[str] = "Itinerary item not found"


class BookingRepository(ScopedRepository[Booking]):
    model = Booking
    scope_column = "trip_id"
    not_found: ClassVar[str] = "Booking not found"


class PhotoRepository(ScopedRepository[TripPhoto]):
    model = TripPhoto
    scope_column = "trip_id"
    not_found: ClassVar[str] = "Photo not found"


class NoteRepository(ScopedRepository[Note]):
    model = Note
    scope_column = "user_id"
    not_found: ClassVar[str] = "Note not found"


class ConversationRepository(ScopedRepository[Conversation]):
    model = Conversation
    scope_column = "user_id"
    not_found: ClassVar[str] = "Conversation not found"


class MessageRepository(ScopedRepository[Message]):
    """Scoped to a conversation that was loaded through ConversationRepository."""

    model = Message
    scope_column = "conversation_id"
    not_found: ClassVar[str] = "Message not found"


class DocumentRepository(ScopedRepository[Document]):
    model = Document
    scope_column = "user_id"
    not_found: ClassVar[str] = "Document not found"


class FeedbackRepository(ScopedRepository[Feedback]):
    model = Feedback
    scope_column = "user_id"
    not_found: ClassVar[str] = "Feedback not found"


__all__ = [
    "BookingRepository",
    "ConversationRepository",
    "DocumentRepository",
    "FeedbackRepository",
    "ItineraryRepository",
    "MessageRepository",
    "NoteRepository",
    "PhotoRepository",
    "ScopedRepository",
    "TripRepository",
    "newest_first",
]
