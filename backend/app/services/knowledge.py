"""Destination knowledge base: Wikivoyage/Wikipedia guide text chunked, embedded and searched with pgvector."""

import re
from dataclasses import dataclass

from sqlmodel import col, func, select
from sqlmodel.ext.asyncio.session import AsyncSession

from app.core.logging import get_logger
from app.integrations.ports import GuideProvider
from app.llm.client import embed
from app.models import KnowledgeChunk

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
    return re.sub(r"\s+", " ", destination.split(",")[0]).strip().lower()


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
    def __init__(self, session: AsyncSession, guides: GuideProvider) -> None:
        self.session = session
        self.guides = guides

    async def ensure_indexed(self, destination: str) -> bool:
        key = destination_key(destination)
        existing = (
            await self.session.exec(
                select(func.count())
                .select_from(KnowledgeChunk)
                .where(KnowledgeChunk.destination == key)
            )
        ).one()
        if existing:
            return True
        guide = await self.guides.guide(destination)
        if guide is None:
            return False
        pieces: list[tuple[str, str]] = [
            ("Overview", c) for c in _chunks("Overview", guide.summary)
        ]
        for section in guide.sections:
            pieces.extend((section.title, c) for c in _chunks(section.title, section.text))
        pieces = pieces[:60]
        vectors = await embed([text for _, text in pieces], task="RETRIEVAL_DOCUMENT")
        for index, ((title, text), vector) in enumerate(zip(pieces, vectors, strict=True)):
            self.session.add(
                KnowledgeChunk(
                    destination=key,
                    source=guide.source,
                    source_url=guide.url,
                    chunk_index=index,
                    title=title,
                    content=text,
                    license=guide.license,
                    embedding=vector,
                )
            )
        await self.session.commit()
        log.info("guide_indexed", destination=key, chunks=len(pieces), source=guide.source)
        return True

    async def search(self, destination: str, query: str, *, k: int = 6) -> list[GuideSnippet]:
        key = destination_key(destination)
        [vector] = await embed([query], task="RETRIEVAL_QUERY")
        rows = await self.session.exec(
            select(KnowledgeChunk)
            .where(KnowledgeChunk.destination == key)
            .order_by(col(KnowledgeChunk.embedding).cosine_distance(vector))
            .limit(k)
        )
        return [
            GuideSnippet(
                title=r.title, text=r.content, url=r.source_url, source=r.source, license=r.license
            )
            for r in rows.all()
        ]
