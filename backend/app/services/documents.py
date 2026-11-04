"""Trip documents (tickets, reservations, visas) in object storage with validated uploads."""

import hashlib
import uuid

from sqlmodel import col
from sqlmodel.ext.asyncio.session import AsyncSession

from app.core.config import settings
from app.core.errors import InvalidInput
from app.integrations.ports import ObjectStorage
from app.models import Document, User
from app.repositories import DocumentRepository, TripRepository, newest_first

# Allowed types are checked against the file's leading bytes, not the client-supplied header.
SIGNATURES: dict[str, tuple[bytes, ...]] = {
    "application/pdf": (b"%PDF-",),
    "image/png": (b"\x89PNG\r\n\x1a\n",),
    "image/jpeg": (b"\xff\xd8\xff",),
    "image/webp": (b"RIFF",),
}


def sniff_content_type(data: bytes) -> str | None:
    for content_type, prefixes in SIGNATURES.items():
        if any(data.startswith(p) for p in prefixes):
            if content_type == "image/webp" and data[8:12] != b"WEBP":
                continue
            return content_type
    return None


def safe_filename(name: str) -> str:
    cleaned = "".join(c for c in name if c.isalnum() or c in "._- ").strip(" .")
    return (cleaned or "document")[:120]


class DocumentService:
    def __init__(self, session: AsyncSession, user: User, storage: ObjectStorage) -> None:
        self.session = session
        self.user = user
        self.storage = storage
        self.documents = DocumentRepository(session, user.id)

    async def for_trip(self, trip_id: uuid.UUID | None) -> list[Document]:
        where = [col(Document.trip_id) == trip_id] if trip_id else []
        return await self.documents.all(*where, order_by=[newest_first(Document)])

    async def upload(self, filename: str, data: bytes, trip_id: uuid.UUID | None) -> Document:
        if len(data) > settings.MAX_UPLOAD_MB * 1024 * 1024:
            raise InvalidInput(f"Files can be at most {settings.MAX_UPLOAD_MB} MB")
        content_type = sniff_content_type(data)
        if content_type is None:
            raise InvalidInput("Only PDF, PNG, JPEG and WebP files are accepted")
        if trip_id is not None:
            await TripRepository(self.session, self.user.id).get(trip_id)
        key = f"documents/{self.user.id}/{uuid.uuid4()}"
        await self.storage.put(key, data, content_type)
        document = await self.documents.add(
            Document(
                user_id=self.user.id,
                trip_id=trip_id,
                filename=safe_filename(filename),
                content_type=content_type,
                size_bytes=len(data),
                sha256=hashlib.sha256(data).hexdigest(),
                storage_key=key,
            )
        )
        await self.session.commit()
        return document

    async def get(self, document_id: uuid.UUID) -> Document:
        return await self.documents.get(document_id)

    async def read(self, document: Document) -> bytes:
        return await self.storage.get(document.storage_key)

    async def download_url(self, document: Document) -> str | None:
        return await self.storage.download_url(document.storage_key, document.filename)

    async def delete(self, document_id: uuid.UUID) -> None:
        document = await self.documents.get(document_id)
        await self.storage.delete(document.storage_key)
        await self.documents.delete(document)
        await self.session.commit()

    async def delete_for_trip(self, trip_id: uuid.UUID) -> None:
        for document in await self.documents.all(col(Document.trip_id) == trip_id):
            await self.storage.delete(document.storage_key)

    async def delete_all(self) -> None:
        for document in await self.documents.all():
            await self.storage.delete(document.storage_key)
