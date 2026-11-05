"""Trip documents (tickets, reservations, visas) in object storage with validated uploads."""

import hashlib
import uuid

import anyio
from sqlalchemy import ColumnElement
from sqlmodel import col, func, select
from sqlmodel.ext.asyncio.session import AsyncSession

from app.core.config import settings
from app.core.errors import InvalidInput, QuotaExceeded, StorageFull
from app.integrations.ports import ObjectStorage
from app.models import Document, User
from app.repositories import DocumentRepository, TripRepository, newest_first

MB = 1024 * 1024

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
        await self._check_quota(len(data))
        key = f"documents/{self.user.id}/{uuid.uuid4()}"
        await self.storage.put(key, data, content_type)
        try:
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
        except BaseException:
            # Bytes without a document row would escape the quota.
            with anyio.CancelScope(shield=True):
                await self.session.rollback()
                await self.storage.delete(key)
            raise
        return document

    async def _check_quota(self, size: int) -> None:
        """Per-user and global byte caps; the user's row lock serialises their own uploads."""
        await self.session.exec(select(User.id).where(User.id == self.user.id).with_for_update())
        quota_mb = (
            settings.STORAGE_QUOTA_ANONYMOUS_MB
            if self.user.is_anonymous
            else settings.STORAGE_QUOTA_MB
        )
        if await self._stored_bytes(col(Document.user_id) == self.user.id) + size > quota_mb * MB:
            hint = " Sign in with an account for more space." if self.user.is_anonymous else ""
            raise QuotaExceeded(
                f"Your documents can take up at most {quota_mb} MB. Delete some files first.{hint}"
            )
        if await self._stored_bytes() + size > settings.STORAGE_TOTAL_MB * MB:
            raise StorageFull("Uploads are paused because the demo's shared storage is full.")

    async def _stored_bytes(self, *where: ColumnElement[bool]) -> int:
        total = func.coalesce(func.sum(col(Document.size_bytes)), 0)
        return int((await self.session.exec(select(total).where(*where))).one())

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
