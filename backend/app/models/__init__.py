"""All tables, imported here so Alembic sees the full metadata."""

from app.models.content import (
    Conversation,
    Document,
    Feedback,
    FeedbackTarget,
    KnowledgeAlias,
    KnowledgeChunk,
    Message,
    MessageRole,
    Note,
    StoredObject,
)
from app.models.trip import (
    Booking,
    BookingKind,
    BookingStatus,
    ItemCategory,
    ItineraryItem,
    Trip,
    TripPace,
    TripPhoto,
    TripStatus,
)
from app.models.user import User

__all__ = [
    "Booking",
    "BookingKind",
    "BookingStatus",
    "Conversation",
    "Document",
    "Feedback",
    "FeedbackTarget",
    "ItemCategory",
    "ItineraryItem",
    "KnowledgeAlias",
    "KnowledgeChunk",
    "Message",
    "MessageRole",
    "Note",
    "StoredObject",
    "Trip",
    "TripPace",
    "TripPhoto",
    "TripStatus",
    "User",
]
