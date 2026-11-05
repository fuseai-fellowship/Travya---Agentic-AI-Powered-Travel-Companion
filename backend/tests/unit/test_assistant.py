import asyncio
import uuid
from types import SimpleNamespace
from typing import Any

import pytest

from app.agents.assistant import agent as assistant
from app.integrations.fakes import FakeGuides


class SlowGeocoder:
    async def search(self, query: str, *, limit: int = 5) -> list[Any]:
        await asyncio.sleep(5)
        return []


def _tools(integrations: Any) -> dict[str, Any]:
    llm = assistant.build_assistant(uuid.uuid4(), integrations, None)
    return {tool.__name__: tool for tool in llm.tools}  # type: ignore[union-attr]


async def test_a_hanging_tool_times_out_with_an_error(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(assistant, "TOOL_TIMEOUT_S", 0.05)
    tools = _tools(SimpleNamespace(geocoder=SlowGeocoder(), guides=FakeGuides()))
    result = await tools["search_places"](destination="Pokhara")
    assert "unavailable" in result["error"]
