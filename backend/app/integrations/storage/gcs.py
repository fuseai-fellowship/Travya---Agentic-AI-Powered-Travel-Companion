"""Google Cloud Storage; blocking client calls run in worker threads.

Signed URLs use the IAM signBlob API with the runtime's default credentials, so they work on
Cloud Run without a key file (the service account needs roles/iam.serviceAccountTokenCreator on itself).
"""

import asyncio
from contextlib import suppress
from datetime import timedelta
from typing import Any
from urllib.parse import quote

import google.auth
from google.api_core.exceptions import NotFound as GcsNotFound
from google.auth.transport.requests import Request
from google.cloud import storage

from app.core.errors import NotFound
from app.core.logging import get_logger
from app.integrations.storage import validate_key

log = get_logger(__name__)

_SCOPES = ["https://www.googleapis.com/auth/cloud-platform"]


def content_disposition(filename: str) -> str:
    """Attachment header with an ASCII fallback and the UTF-8 name (RFC 6266)."""
    cleaned = "".join(ch for ch in filename if ch.isprintable() and ch not in '"\\/') or "download"
    fallback = cleaned.encode("ascii", "replace").decode().replace("?", "_")
    return f"attachment; filename=\"{fallback}\"; filename*=UTF-8''{quote(cleaned)}"


class GcsStorage:
    def __init__(self, bucket: str, client: Any = None) -> None:
        self._bucket_name = bucket
        self._client = client
        self._credentials: Any = None

    def _bucket(self) -> Any:
        if self._client is None:
            self._client = storage.Client()
        return self._client.bucket(self._bucket_name)

    def _blob(self, key: str) -> Any:
        return self._bucket().blob(validate_key(key))

    async def put(self, key: str, data: bytes, content_type: str) -> None:
        blob = self._blob(key)
        await asyncio.to_thread(blob.upload_from_string, data, content_type=content_type)

    async def get(self, key: str) -> bytes:
        blob = self._blob(key)
        try:
            data: bytes = await asyncio.to_thread(blob.download_as_bytes)
        except GcsNotFound as exc:
            raise NotFound("File not found") from exc
        return data

    async def delete(self, key: str) -> None:
        blob = self._blob(key)
        with suppress(GcsNotFound):
            await asyncio.to_thread(blob.delete)

    async def download_url(self, key: str, filename: str, expires_s: int = 600) -> str | None:
        blob = self._blob(key)
        return await asyncio.to_thread(self._sign, blob, filename, expires_s)

    def _sign(self, blob: Any, filename: str, expires_s: int) -> str | None:
        credentials = self._fresh_credentials()
        email = getattr(credentials, "service_account_email", None)
        if not email:
            # e.g. local user credentials from gcloud: let the API stream the file instead
            log.warning("gcs_signing_unavailable", reason="credentials have no service account")
            return None
        url: str = blob.generate_signed_url(
            version="v4",
            expiration=timedelta(seconds=expires_s),
            method="GET",
            response_disposition=content_disposition(filename),
            service_account_email=email,
            access_token=credentials.token,
        )
        return url

    def _fresh_credentials(self) -> Any:
        if self._credentials is None:
            self._credentials, _ = google.auth.default(scopes=_SCOPES)
        if not self._credentials.valid:
            self._credentials.refresh(Request())
        return self._credentials
