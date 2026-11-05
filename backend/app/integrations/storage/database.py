"""Files kept in Postgres, for hosts without durable disk or object storage (e.g. Hugging Face Spaces).

Fine for a demo's documents (uploads are capped at MAX_UPLOAD_MB); use GCS where it is available.
"""

from sqlmodel import col, delete, select

from app.core.db import SessionFactory
from app.core.errors import NotFound
from app.integrations.storage import validate_key
from app.models import StoredObject


class DatabaseStorage:
    async def put(self, key: str, data: bytes, content_type: str) -> None:
        key = validate_key(key)
        async with SessionFactory() as session:
            existing = await session.get(StoredObject, key)
            if existing is None:
                session.add(StoredObject(key=key, content_type=content_type, data=data))
            else:
                existing.content_type, existing.data = content_type, data
                session.add(existing)
            await session.commit()

    async def get(self, key: str) -> bytes:
        async with SessionFactory() as session:
            row = (
                await session.exec(
                    select(StoredObject.data).where(col(StoredObject.key) == validate_key(key))
                )
            ).first()
        if row is None:
            raise NotFound("File not found")
        return bytes(row)

    async def delete(self, key: str) -> None:
        async with SessionFactory() as session:
            await session.exec(
                delete(StoredObject).where(col(StoredObject.key) == validate_key(key))
            )
            await session.commit()

    async def download_url(self, key: str, filename: str, expires_s: int = 600) -> str | None:
        validate_key(key)
        return None  # the API streams the bytes itself
