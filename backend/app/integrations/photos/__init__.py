"""Destination photos: Unsplash with an access key, Wikimedia Commons otherwise or as the fallback."""

from app.core.errors import UpstreamUnavailable
from app.core.logging import get_logger
from app.integrations.ports import Photo, PhotoProvider

log = get_logger(__name__)


class FallbackPhotos:
    """Searches the primary provider; the fallback covers outages and empty results."""

    def __init__(self, primary: PhotoProvider, fallback: PhotoProvider) -> None:
        self._primary = primary
        self._fallback = fallback

    async def search(self, query: str, *, limit: int = 6) -> list[Photo]:
        try:
            photos = await self._primary.search(query, limit=limit)
        except UpstreamUnavailable:
            log.warning("photos_fallback", query=query)
            photos = []
        return photos or await self._fallback.search(query, limit=limit)

    async def track_download(self, photo: Photo) -> None:
        # each provider ignores photos that are not its own
        await self._primary.track_download(photo)
        await self._fallback.track_download(photo)
