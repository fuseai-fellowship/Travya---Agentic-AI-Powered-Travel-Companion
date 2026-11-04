"""User content outside trips: chat, notes, documents, feedback; plus the shared guide knowledge base."""

import uuid
from datetime import datetime
from enum import StrEnum
from typing import Any

from pgvector.sqlalchemy import Vector
from sqlalchemy import Column, Index, SmallInteger, String, Text, UniqueConstraint
from sqlalchemy.dialects.postgresql import JSONB
from sqlmodel import Field

from app.models.base import Table, created_at_field, id_field, updated_at_field

EMBEDDING_DIM = 768


class MessageRole(StrEnum):
    user = "user"
    assistant = "assistant"


class Conversation(Table, table=True):
    __tablename__ = "conversations"

    id: uuid.UUID = id_field()
    user_id: uuid.UUID = Field(foreign_key="users.id", ondelete="CASCADE", index=True)
    trip_id: uuid.UUID | None = Field(
        default=None, foreign_key="trips.id", ondelete="SET NULL", index=True
    )
    title: str = Field(default="New conversation", max_length=200)
    is_archived: bool = False
    is_favorite: bool = False
    last_message_at: datetime = created_at_field()
    created_at: datetime = created_at_field()
    updated_at: datetime = updated_at_field()


class Message(Table, table=True):
    __tablename__ = "messages"

    id: uuid.UUID = id_field()
    conversation_id: uuid.UUID = Field(
        foreign_key="conversations.id", ondelete="CASCADE", index=True
    )
    role: MessageRole = Field(sa_type=String(16))
    content: str = Field(sa_type=Text)
    meta: dict[str, Any] = Field(default_factory=dict, sa_type=JSONB)
    created_at: datetime = created_at_field()


class Note(Table, table=True):
    __tablename__ = "notes"

    id: uuid.UUID = id_field()
    user_id: uuid.UUID = Field(foreign_key="users.id", ondelete="CASCADE", index=True)
    trip_id: uuid.UUID | None = Field(
        default=None, foreign_key="trips.id", ondelete="SET NULL", index=True
    )
    title: str = Field(max_length=200)
    content: str = Field(default="", sa_type=Text)
    color: str = Field(default="yellow", max_length=16)
    is_pinned: bool = False
    created_at: datetime = created_at_field()
    updated_at: datetime = updated_at_field()


class Document(Table, table=True):
    __tablename__ = "documents"

    id: uuid.UUID = id_field()
    user_id: uuid.UUID = Field(foreign_key="users.id", ondelete="CASCADE", index=True)
    trip_id: uuid.UUID | None = Field(
        default=None, foreign_key="trips.id", ondelete="CASCADE", index=True
    )
    filename: str = Field(max_length=255)
    content_type: str = Field(max_length=100)
    size_bytes: int
    sha256: str = Field(max_length=64)
    storage_key: str = Field(max_length=300, unique=True)
    created_at: datetime = created_at_field()


class FeedbackTarget(StrEnum):
    trip_plan = "trip_plan"
    message = "message"


class Feedback(Table, table=True):
    __tablename__ = "feedback"
    __table_args__ = (UniqueConstraint("user_id", "target_type", "target_id"),)

    id: uuid.UUID = id_field()
    user_id: uuid.UUID = Field(foreign_key="users.id", ondelete="CASCADE", index=True)
    target_type: FeedbackTarget = Field(sa_type=String(16))
    target_id: uuid.UUID
    rating: int = Field(ge=1, le=5, sa_type=SmallInteger)
    comment: str | None = Field(default=None, max_length=1000)
    created_at: datetime = created_at_field()


class KnowledgeChunk(Table, table=True):
    """Public destination guide text (Wikivoyage, curated seed) embedded for retrieval."""

    __tablename__ = "knowledge_chunks"
    __table_args__ = (
        UniqueConstraint("source_url", "chunk_index"),
        Index(
            "ix_knowledge_chunks_embedding_hnsw",
            "embedding",
            postgresql_using="hnsw",
            postgresql_ops={"embedding": "vector_cosine_ops"},
        ),
    )

    id: uuid.UUID = id_field()
    destination: str = Field(max_length=200, index=True)
    source: str = Field(max_length=32)
    source_url: str = Field(max_length=1000)
    chunk_index: int = 0
    title: str = Field(max_length=300)
    content: str = Field(sa_type=Text)
    license: str = Field(default="CC BY-SA 4.0", max_length=64)
    embedding: list[float] = Field(sa_column=Column(Vector(EMBEDDING_DIM), nullable=False))
    created_at: datetime = created_at_field()
