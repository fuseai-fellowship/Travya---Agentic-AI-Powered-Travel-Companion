from datetime import timedelta
from pathlib import Path
from typing import Any
from unittest.mock import MagicMock

import anyio
import pytest
from google.api_core.exceptions import NotFound as GcsNotFound

from app.core.errors import InvalidInput, NotFound
from app.integrations.fakes import MemoryStorage
from app.integrations.storage import content_disposition
from app.integrations.storage.gcs import GcsStorage
from app.integrations.storage.local import LocalStorage

BAD_KEYS = [
    "",
    "/etc/passwd",
    "../secrets.txt",
    "trips/../../escape.pdf",
    "trips/./doc.pdf",
    "trips//doc.pdf",
    "trips\\doc.pdf",
    "trips/doc.pdf/..",
    "nul\x00byte",
]


async def test_local_round_trip(tmp_path: Path) -> None:
    storage = LocalStorage(tmp_path / "files")

    await storage.put("trips/42/ticket.pdf", b"%PDF-1.7", "application/pdf")

    assert await anyio.Path(tmp_path / "files/trips/42/ticket.pdf").read_bytes() == b"%PDF-1.7"
    assert await storage.get("trips/42/ticket.pdf") == b"%PDF-1.7"
    assert await storage.download_url("trips/42/ticket.pdf", "ticket.pdf") is None
    await storage.put("trips/42/ticket.pdf", b"v2", "application/pdf")
    assert await storage.get("trips/42/ticket.pdf") == b"v2"
    assert [p.name async for p in anyio.Path(tmp_path / "files/trips/42").iterdir()] == [
        "ticket.pdf"
    ]

    await storage.delete("trips/42/ticket.pdf")
    await storage.delete("trips/42/ticket.pdf")
    with pytest.raises(NotFound):
        await storage.get("trips/42/ticket.pdf")


@pytest.mark.parametrize("key", BAD_KEYS)
async def test_local_rejects_path_traversal(tmp_path: Path, key: str) -> None:
    storage = LocalStorage(tmp_path)
    with pytest.raises(InvalidInput):
        await storage.put(key, b"x", "text/plain")
    with pytest.raises(InvalidInput):
        await storage.get(key)
    with pytest.raises(InvalidInput):
        await storage.delete(key)
    assert [path async for path in anyio.Path(tmp_path).iterdir()] == []


@pytest.mark.parametrize("key", BAD_KEYS)
async def test_memory_storage_rejects_bad_keys(key: str) -> None:
    with pytest.raises(InvalidInput):
        await MemoryStorage().put(key, b"x", "text/plain")


def test_content_disposition() -> None:
    assert content_disposition("ticket.pdf") == (
        "attachment; filename=\"ticket.pdf\"; filename*=UTF-8''ticket.pdf"
    )
    assert content_disposition('Kathmandu "trip".pdf') == (
        "attachment; filename=\"Kathmandu trip.pdf\"; filename*=UTF-8''Kathmandu%20trip.pdf"
    )
    assert content_disposition("Zürich.pdf").startswith('attachment; filename="Z_rich.pdf"')
    header = content_disposition("日本.pdf")
    assert header == "attachment; filename=\"__.pdf\"; filename*=UTF-8''%E6%97%A5%E6%9C%AC.pdf"
    header.encode("latin-1")  # what Starlette does with header values


class _Credentials:
    def __init__(self) -> None:
        self.valid = False
        self.token: str | None = None
        self.service_account_email = "default"

    def refresh(self, request: Any) -> None:
        self.valid = True
        self.token = "ya29.token"
        self.service_account_email = "travya-api@demo-travya.iam.gserviceaccount.com"


def _gcs(blob: MagicMock) -> GcsStorage:
    client = MagicMock()
    client.bucket.return_value.blob.return_value = blob
    return GcsStorage("travya-docs", client=client)


async def test_gcs_signed_url_uses_default_credentials(monkeypatch: pytest.MonkeyPatch) -> None:
    credentials = _Credentials()
    monkeypatch.setattr("google.auth.default", lambda scopes: (credentials, "demo-travya"))
    blob = MagicMock()
    blob.generate_signed_url.return_value = (
        "https://storage.googleapis.com/travya-docs/k?X-Goog-Signature=abc"
    )

    url = await _gcs(blob).download_url("trips/1/visa.pdf", "visa.pdf", expires_s=300)

    assert url == "https://storage.googleapis.com/travya-docs/k?X-Goog-Signature=abc"
    blob.generate_signed_url.assert_called_once_with(
        version="v4",
        expiration=timedelta(seconds=300),
        method="GET",
        response_disposition="attachment; filename=\"visa.pdf\"; filename*=UTF-8''visa.pdf",
        service_account_email="travya-api@demo-travya.iam.gserviceaccount.com",
        access_token="ya29.token",
    )


async def test_gcs_put_get_delete() -> None:
    blob = MagicMock()
    blob.download_as_bytes.return_value = b"data"
    storage = _gcs(blob)

    await storage.put("trips/1/a.pdf", b"data", "application/pdf")
    blob.upload_from_string.assert_called_once_with(b"data", content_type="application/pdf")
    assert await storage.get("trips/1/a.pdf") == b"data"

    blob.download_as_bytes.side_effect = GcsNotFound("gone")  # type: ignore[no-untyped-call]
    with pytest.raises(NotFound):
        await storage.get("trips/1/a.pdf")
    blob.delete.side_effect = GcsNotFound("gone")  # type: ignore[no-untyped-call]
    await storage.delete("trips/1/a.pdf")


async def test_gcs_rejects_bad_keys() -> None:
    with pytest.raises(InvalidInput):
        await _gcs(MagicMock()).put("../x", b"", "text/plain")
