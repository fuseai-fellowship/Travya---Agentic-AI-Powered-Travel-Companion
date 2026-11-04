"""Object storage for trip documents: local disk in development, Google Cloud Storage in production."""

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
