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


def test_only_recent_turns_are_sent_to_the_model() -> None:
    from google.adk.models.llm_request import LlmRequest
    from google.genai import types

    def text(role: str, value: str) -> types.Content:
        return types.Content(role=role, parts=[types.Part(text=value)])

    contents = []
    for turn in range(20):
        contents.append(text("user", f"question {turn}"))
        contents.append(
            types.Content(
                role="model",
                parts=[types.Part(function_call=types.FunctionCall(name="my_trips", args={}))],
            )
        )
        contents.append(
            types.Content(
                role="user",
                parts=[
                    types.Part(
                        function_response=types.FunctionResponse(name="my_trips", response={})
                    )
                ],
            )
        )
        contents.append(text("model", f"answer {turn}"))
    request = LlmRequest(contents=contents)
    assistant.keep_recent_turns(None, request)  # type: ignore[arg-type]
    assert len(request.contents) == assistant.MAX_TURNS * 4
    first = request.contents[0]
    assert first.parts and first.parts[0].text == f"question {20 - assistant.MAX_TURNS}"
