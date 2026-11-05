"""Freely licensed photos from Wikimedia Commons (keyless)."""

import html
import re
from typing import Any

import httpx
from cashews import cache

from app.integrations.caching import PHOTOS_TTL, non_empty
from app.integrations.http import fetch_json
from app.integrations.ports import Photo

API_URL = "https://commons.wikimedia.org/w/api.php"
COMMONS_URL = "https://commons.wikimedia.org"
THUMB_WIDTH = 800
MIN_WIDTH = 400
_BITMAP_SUFFIXES = (".jpg", ".jpeg", ".png", ".webp")
_TAG = re.compile(r"<[^>]+>")
_HREF = re.compile(r'href="([^"]+)"')


class WikimediaPhotos:
    def __init__(self, http: httpx.AsyncClient, api_url: str = API_URL) -> None:
        self._http = http
        self._api_url = api_url

    @cache(ttl=PHOTOS_TTL, key="wikimedia:{query:lower}:{limit}", condition=non_empty)
    async def search(self, query: str, *, limit: int = 6) -> list[Photo]:
        params = {
            "action": "query",
            "format": "json",
            "formatversion": 2,
            "generator": "search",
            "gsrsearch": f"{query} filetype:bitmap",
            "gsrnamespace": 6,
            # extra results leave room for skipping drawings and small files
            "gsrlimit": min(limit * 2, 50),
            "prop": "imageinfo",
            "iiprop": "url|size|extmetadata",
            "iiurlwidth": THUMB_WIDTH,
            "iiextmetadatafilter": "Artist|ImageDescription|LicenseShortName",
        }
        data = await fetch_json(self._http, "GET", self._api_url, params=params)
        pages: list[dict[str, Any]] = (data.get("query") or {}).get("pages") or []
        pages.sort(key=lambda page: page.get("index", 0))
        photos = [photo for photo in map(to_photo, pages) if photo is not None]
        return photos[:limit]

    async def track_download(self, photo: Photo) -> None:
        return None


def to_photo(page: dict[str, Any]) -> Photo | None:
    title: str = page.get("title") or ""
    info: dict[str, Any] = (page.get("imageinfo") or [{}])[0]
    url = info.get("thumburl") or info.get("url")
    width = info.get("thumbwidth") or info.get("width") or 0
    if not title.lower().endswith(_BITMAP_SUFFIXES) or not url or width < MIN_WIDTH:
        return None
    metadata: dict[str, dict[str, Any]] = info.get("extmetadata") or {}
    artist = str((metadata.get("Artist") or {}).get("value") or "")
    description = plain_text(str((metadata.get("ImageDescription") or {}).get("value") or ""))
    return Photo(
        url=url,
        thumb_url=url,
        width=width,
        height=info.get("thumbheight") or info.get("height") or 0,
        alt=description[:200] or title.removeprefix("File:").rsplit(".", 1)[0],
        author_name=plain_text(artist) or "Wikimedia Commons contributor",
        author_url=_author_url(artist),
        source="wikimedia",
        source_url=info.get("descriptionurl") or f"{COMMONS_URL}/wiki/{title.replace(' ', '_')}",
    )


def plain_text(markup: str) -> str:
    return " ".join(html.unescape(_TAG.sub(" ", markup)).split())


def _author_url(artist: str) -> str | None:
    match = _HREF.search(artist)
    if not match:
        return None
    href = html.unescape(match.group(1))
    if href.startswith("//"):
        return f"https:{href}"
    if href.startswith("/"):
        return f"{COMMONS_URL}{href}"
    return href if href.startswith(("https://", "http://")) else None
