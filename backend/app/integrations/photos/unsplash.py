"""Unsplash photo search, following the API guidelines.

Photos are hotlinked from `urls`, photographer and photo links carry the referral UTM parameters,
and `track_download` must be called when a user picks a photo (it hits `download_location`).
"""

from typing import Any

import httpx
from cashews import cache

from app.core.errors import UpstreamUnavailable
from app.core.logging import get_logger
from app.integrations.caching import PHOTOS_TTL, non_empty
from app.integrations.http import fetch_json, send_with_retry
from app.integrations.ports import Photo

log = get_logger(__name__)

API_URL = "https://api.unsplash.com"
UTM_PARAMS = "utm_source=travya&utm_medium=referral"
REGULAR_WIDTH = 1080
MAX_PER_PAGE = 30


def with_utm(url: str) -> str:
    return f"{url}{'&' if '?' in url else '?'}{UTM_PARAMS}"


class UnsplashPhotos:
    def __init__(self, http: httpx.AsyncClient, access_key: str, base_url: str = API_URL) -> None:
        self._http = http
        self._access_key = access_key
        self._base_url = base_url.rstrip("/")

    def _headers(self) -> dict[str, str]:
        return {"Authorization": f"Client-ID {self._access_key}", "Accept-Version": "v1"}

    @cache(ttl=PHOTOS_TTL, key="unsplash:{query:lower}:{limit}", condition=non_empty)
    async def search(self, query: str, *, limit: int = 6) -> list[Photo]:
        params = {
            "query": query,
            "per_page": min(limit, MAX_PER_PAGE),
            "orientation": "landscape",
            "content_filter": "high",
        }
        data = await fetch_json(
            self._http,
            "GET",
            f"{self._base_url}/search/photos",
            params=params,
            headers=self._headers(),
        )
        return [to_photo(item, query) for item in data.get("results", [])][:limit]

    async def track_download(self, photo: Photo) -> None:
        if photo.source != "unsplash" or not photo.download_location:
            return
        url = httpx.URL(photo.download_location)
        # the access key must only ever go to Unsplash itself
        if url.scheme != "https" or url.host != httpx.URL(self._base_url).host:
            log.warning("unsplash_download_location_rejected", host=url.host)
            return
        try:
            await send_with_retry(self._http, "GET", str(url), headers=self._headers())
        except UpstreamUnavailable:
            log.warning("unsplash_track_download_failed")


def to_photo(item: dict[str, Any], query: str) -> Photo:
    urls, links, user = item["urls"], item["links"], item["user"]
    width, height = item.get("width") or 0, item.get("height") or 0
    # `urls.regular` is 1080 px wide; report the size of the image we hotlink
    regular_height = round(REGULAR_WIDTH * height / width) if width and height else 720
    return Photo(
        url=urls["regular"],
        thumb_url=urls["small"],
        width=REGULAR_WIDTH,
        height=regular_height,
        alt=item.get("alt_description") or item.get("description") or query,
        author_name=user.get("name") or user.get("username") or "Unsplash photographer",
        author_url=with_utm(user["links"]["html"]) if user.get("links") else None,
        source="unsplash",
        source_url=with_utm(links["html"]),
        download_location=links.get("download_location"),
    )
