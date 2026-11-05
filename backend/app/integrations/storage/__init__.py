"""Object storage for trip documents: local disk in development, Google Cloud Storage in production."""

from urllib.parse import quote

from app.core.errors import InvalidInput


def validate_key(key: str) -> str:
    """Keys are relative, slash-separated paths; anything that could escape the root is rejected."""
    parts = key.split("/")
    if (
        not key
        or key.startswith("/")
        or "\\" in key
        or "\x00" in key
        or any(part in ("", ".", "..") for part in parts)
    ):
        raise InvalidInput("Invalid storage key")
    return key


def content_disposition(filename: str) -> str:
    """Attachment header with an ASCII fallback and the UTF-8 name (RFC 6266); safe to send
    as a latin-1 header whatever the file is called."""
    cleaned = "".join(ch for ch in filename if ch.isprintable() and ch not in '"\\/') or "download"
    fallback = cleaned.encode("ascii", "replace").decode().replace("?", "_")
    return f"attachment; filename=\"{fallback}\"; filename*=UTF-8''{quote(cleaned)}"
