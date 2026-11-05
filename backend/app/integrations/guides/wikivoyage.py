"""Destination guides from English Wikivoyage, with a Wikipedia summary as the fallback.

Both are CC BY-SA 4.0: the UI must show the source link and licence.
"""

import re
from typing import Any
from urllib.parse import quote

import httpx
from cashews import cache

from app.integrations.caching import GUIDE_TTL, non_empty
from app.integrations.http import fetch_json, parse_json, send_with_retry
from app.integrations.ports import DestinationGuide, GuideSection

WIKIVOYAGE_API = "https://en.wikivoyage.org/w/api.php"
WIKIVOYAGE_PAGE = "https://en.wikivoyage.org/wiki/"
WIKIPEDIA_REST = "https://en.wikipedia.org/api/rest_v1"
WIKIPEDIA_PAGE = "https://en.wikipedia.org/wiki/"
KEEP_SECTIONS = (
    "Understand",
    "Get around",
    "See",
    "Do",
    "Eat",
    "Drink",
    "Sleep",
    "Stay safe",
    "Respect",
)
SECTION_CHARS = 1500
SUMMARY_CHARS = 1200

_HEADING = re.compile(r"^(={2,6})\s*(.+?)\s*\1\s*$", re.MULTILINE)
_BLANK_LINES = re.compile(r"\n{3,}")


class WikivoyageGuides:
    def __init__(
        self,
        http: httpx.AsyncClient,
        *,
        wikivoyage_api: str = WIKIVOYAGE_API,
        wikipedia_rest: str = WIKIPEDIA_REST,
    ) -> None:
        self._http = http
        self._wikivoyage_api = wikivoyage_api
        self._wikipedia_rest = wikipedia_rest.rstrip("/")

    @cache(ttl=GUIDE_TTL, key="guide:{destination:lower}", condition=non_empty)
    async def guide(self, destination: str) -> DestinationGuide | None:
        title = page_title(destination)
        if not title:
            return None
        return await self._wikivoyage(title) or await self._wikipedia(title)

    async def _wikivoyage(self, title: str) -> DestinationGuide | None:
        params = {
            "action": "query",
            "prop": "extracts|pageprops",
            "ppprop": "disambiguation",
            "explaintext": 1,
            "redirects": 1,
            "format": "json",
            "formatversion": 2,
            "titles": title,
        }
        data = await fetch_json(self._http, "GET", self._wikivoyage_api, params=params)
        pages: list[dict[str, Any]] = (data.get("query") or {}).get("pages") or []
        page = pages[0] if pages else {}
        if page.get("missing") or "disambiguation" in (page.get("pageprops") or {}):
            return None
        summary, sections = parse_extract(page.get("extract") or "")
        if not summary:
            return None
        return DestinationGuide(
            destination=page["title"],
            summary=summary,
            sections=sections,
            url=_page_url(WIKIVOYAGE_PAGE, page["title"]),
            source="wikivoyage",
        )

    async def _wikipedia(self, title: str) -> DestinationGuide | None:
        url = f"{self._wikipedia_rest}/page/summary/{quote(_slug(title), safe='')}"
        response = await send_with_retry(self._http, "GET", url)
        if response.status_code == 404:
            return None
        data = parse_json(response)
        if data.get("type") == "disambiguation" or not data.get("extract"):
            return None
        canonical = data.get("title") or title
        page_url = ((data.get("content_urls") or {}).get("desktop") or {}).get("page")
        return DestinationGuide(
            destination=canonical,
            summary=data["extract"],
            sections=[],
            url=page_url or _page_url(WIKIPEDIA_PAGE, canonical),
            source="wikipedia",
        )


def page_title(destination: str) -> str:
    """Wiki page titles are case-sensitive after the first letter; capitalise all-lowercase input."""
    title = " ".join(destination.split())
    if title.islower():
        title = " ".join(word[:1].upper() + word[1:] for word in title.split(" "))
    return title


def parse_extract(text: str) -> tuple[str, list[GuideSection]]:
    """Split a plain-text extract into the intro and the useful level-2 sections."""
    headings = list(_HEADING.finditer(text))
    intro = text[: headings[0].start()] if headings else text
    paragraphs = [p.strip() for p in intro.split("\n") if p.strip()]
    summary = trim("\n\n".join(paragraphs[:2]), SUMMARY_CHARS)

    sections: list[GuideSection] = []
    level2 = [h for h in headings if len(h.group(1)) == 2]
    for heading, following in zip(level2, [*level2[1:], None], strict=True):
        title = heading.group(2)
        if title not in KEEP_SECTIONS:
            continue
        body = text[heading.end() : following.start() if following else len(text)]
        body = _HEADING.sub(lambda m: m.group(2), body)
        body = _BLANK_LINES.sub("\n\n", body).strip()
        if body:
            sections.append(GuideSection(title=title, text=trim(body, SECTION_CHARS)))
    return summary, sections


def trim(text: str, limit: int) -> str:
    """Cut to about `limit` characters, at a sentence or line end when one is close."""
    text = text.strip()
    if len(text) <= limit:
        return text
    cut = text[:limit]
    stop = max(cut.rfind(". "), cut.rfind(".\n"), cut.rfind("\n"))
    if stop > limit * 0.6:
        cut = cut[: stop + 1]
    return cut.rstrip() + " …"


def _slug(title: str) -> str:
    return title.replace(" ", "_")


def _page_url(base: str, title: str) -> str:
    return base + quote(_slug(title), safe="(),:'")
