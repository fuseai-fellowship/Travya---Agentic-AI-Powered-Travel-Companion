"""Destination knowledge base: Wikivoyage/Wikipedia guide text chunked, embedded and searched with pgvector."""

import re
from collections.abc import Callable
from dataclasses import dataclass
from typing import Any, cast

from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.exc import IntegrityError
from sqlmodel import col, delete, func, select
from sqlmodel.ext.asyncio.session import AsyncSession

from app.core.config import settings
from app.core.db import SessionFactory
from app.core.logging import get_logger
from app.integrations.ports import DestinationGuide, GuideProvider
from app.llm.client import embed
from app.models import KnowledgeAlias, KnowledgeChunk

log = get_logger(__name__)

CHUNK_CHARS = 900


@dataclass(frozen=True, slots=True)
class GuideSnippet:
    title: str
    text: str
    url: str
    source: str
    license: str


def destination_key(destination: str) -> str:
    """The alias for a destination as typed: "Paris, Texas" and "Paris" are different aliases."""
    return re.sub(r"\s+", " ", destination).strip().lower()[:200]


def _chunks(title: str, text: str) -> list[str]:
    paragraphs = [p.strip() for p in text.split("\n") if p.strip()]
    chunks: list[str] = []
    current = ""
    for paragraph in paragraphs:
        if current and len(current) + len(paragraph) > CHUNK_CHARS:
            chunks.append(current)
            current = ""
        current = f"{current}\n{paragraph}".strip()
    if current:
        chunks.append(current)
    return [f"{title}: {c}" for c in chunks]


class KnowledgeService:
    """Each read or write uses its own short session, so no connection sits idle in a
    transaction while guides are fetched, texts embedded or agents wait on a model."""

    def __init__(
        self,
        guides: GuideProvider,
        sessions: Callable[[], AsyncSession] = SessionFactory,
    ) -> None:
        self.guides = guides
        self.sessions = sessions

    def _usable(self) -> list[Any]:
        # Offline sample guides can share a local database with live runs; live mode skips them.
        return [] if settings.OFFLINE_INTEGRATIONS else [col(KnowledgeChunk.source) != "fake"]

    async def _indexed(self, session: AsyncSession, source_url: str) -> bool:
        query = (
            select(func.count())
            .select_from(KnowledgeChunk)
            .where(col(KnowledgeChunk.source_url) == source_url, *self._usable())
        )
        return bool((await session.exec(query)).one())

    async def ensure_indexed(self, destination: str) -> str | None:
        """The source URL of the destination's guide, fetched and embedded once per page.

        Chunks are keyed by the guide's canonical URL and each destination name maps to it, so
        "NYC" and "New York City" share one page that is embedded once.
        """
        alias = destination_key(destination)
        async with self.sessions() as session:
            known = await session.get(KnowledgeAlias, alias)
            if known is not None and await self._indexed(session, known.source_url):
                return known.source_url
        # "Pokhara, Nepal" → the "Pokhara" article, falling back to the full name.
        short = destination.split(",")[0].strip()
        guide = await self.guides.guide(short) or (
            await self.guides.guide(destination) if short != destination else None
        )
        if guide is None:
            return None
        async with self.sessions() as session:
            indexed = await self._indexed(session, guide.url)
        if not indexed:
            await self._index(destination, guide)
        async with self.sessions() as session:
            await session.exec(
                insert(KnowledgeAlias)
                .values(alias=alias, source_url=guide.url)
                .on_conflict_do_update(
                    index_elements=[col(KnowledgeAlias.alias)],
                    set_={"source_url": guide.url},
                )
            )
            await session.commit()
        return guide.url

    async def _index(self, destination: str, guide: DestinationGuide) -> None:
        pieces: list[tuple[str, str]] = [
            ("Overview", c) for c in _chunks("Overview", guide.summary)
        ]
        for section in guide.sections:
            pieces.extend((section.title, c) for c in _chunks(section.title, section.text))
        pieces = pieces[:60]
        vectors = await embed([text for _, text in pieces], task="RETRIEVAL_DOCUMENT")
        async with self.sessions() as session:
            if not settings.OFFLINE_INTEGRATIONS:
                # Sample text for the same page (offline demos on a shared database) makes way.
                await session.exec(
                    delete(KnowledgeChunk).where(
                        col(KnowledgeChunk.source_url) == guide.url,
                        col(KnowledgeChunk.source) == "fake",
                    )
                )
            session.add_all(
                KnowledgeChunk(
                    destination=destination_key(destination.split(",")[0]),
                    source=guide.source,
                    source_url=guide.url,
                    chunk_index=index,
                    title=title,
                    content=text,
                    license=guide.license,
                    embedding=vector,
                )
                for index, ((title, text), vector) in enumerate(zip(pieces, vectors, strict=True))
            )
            try:
                await session.commit()
            except IntegrityError:
                # Another request indexed the same page first; its rows serve this one too.
                await session.rollback()
                return
        log.info("guide_indexed", url=guide.url, chunks=len(pieces), source=guide.source)

    async def search(self, source_url: str, query: str, *, k: int = 6) -> list[GuideSnippet]:
        """The passages of one guide (from `ensure_indexed`) closest to the query."""
        [vector] = await embed([query], task="RETRIEVAL_QUERY")
        async with self.sessions() as session:
            rows = (
                await session.exec(
                    select(KnowledgeChunk)
                    .where(col(KnowledgeChunk.source_url) == source_url, *self._usable())
                    .order_by(cast("Any", KnowledgeChunk.embedding).cosine_distance(vector))
                    .limit(k)
                )
            ).all()
        return [
            GuideSnippet(
                title=r.title, text=r.content, url=r.source_url, source=r.source, license=r.license
            )
            for r in rows
        ]
