"""Files under LOCAL_STORAGE_DIR; the API streams them itself (no signed URLs)."""

from pathlib import Path
from uuid import uuid4

import anyio

from app.core.errors import NotFound
from app.integrations.storage import validate_key


class LocalStorage:
    def __init__(self, root: str | Path) -> None:
        self._root = Path(root).resolve()

    def _path(self, key: str) -> anyio.Path:
        return anyio.Path(self._root / validate_key(key))

    async def put(self, key: str, data: bytes, content_type: str) -> None:
        path = self._path(key)
        await path.parent.mkdir(parents=True, exist_ok=True)
        partial = path.with_name(f".{path.name}.{uuid4().hex}.partial")
        await partial.write_bytes(data)
        await partial.replace(path)

    async def get(self, key: str) -> bytes:
        try:
            return await self._path(key).read_bytes()
        except FileNotFoundError as exc:
            raise NotFound("File not found") from exc

    async def delete(self, key: str) -> None:
        await self._path(key).unlink(missing_ok=True)

    async def download_url(self, key: str, filename: str, expires_s: int = 600) -> str | None:
        validate_key(key)
        return None
