"""The guide knowledge base: pages embedded once, whatever name the destination is given."""

from typing import Any

import pytest

from app.integrations.ports import DestinationGuide, GuideSection
from app.services import knowledge as knowledge_module
from app.services.knowledge import KnowledgeService

pytestmark = pytest.mark.db

NYC = DestinationGuide(
    destination="New York City",
    summary="The city that never sleeps.",
    sections=[GuideSection(title="Eat", text="Pizza by the slice and bagels everywhere.")],
    url="https://en.wikivoyage.org/wiki/New_York_City",
    source="wikivoyage",
)


class Guides:
    """Wikivoyage follows redirects: "NYC" and "New York City" are the same page."""

    def __init__(self) -> None:
        self.calls: list[str] = []

    async def guide(self, destination: str) -> DestinationGuide | None:
        self.calls.append(destination)
        return NYC if destination in ("NYC", "New York City") else None


async def test_aliases_share_one_embedded_page(
    clean_db: None, monkeypatch: pytest.MonkeyPatch
) -> None:
    embedded: list[str] = []
    real_embed = knowledge_module.embed

    async def counting_embed(texts: Any, *, task: Any) -> list[list[float]]:
        if task == "RETRIEVAL_DOCUMENT":
            embedded.extend(texts)
        return await real_embed(texts, task=task)

    monkeypatch.setattr(knowledge_module, "embed", counting_embed)
    guides = Guides()
    knowledge = KnowledgeService(guides)  # type: ignore[arg-type]

    assert await knowledge.ensure_indexed("New York City") == NYC.url
    chunks = len(embedded)
    assert chunks > 0
    assert await knowledge.ensure_indexed("NYC") == NYC.url
    assert len(embedded) == chunks  # the page was already there
    assert await knowledge.ensure_indexed("nyc") == NYC.url
    assert guides.calls == ["New York City", "NYC"]  # "nyc" resolved from its alias

    snippets = await knowledge.search(NYC.url, "food")
    assert any("bagels" in s.text for s in snippets)
    assert await knowledge.ensure_indexed("Atlantis") is None
