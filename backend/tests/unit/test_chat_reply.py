"""ChatService.reply online, with a scripted streaming model and the database write recorded."""

import asyncio
import uuid
from collections.abc import AsyncGenerator
from typing import Any

import pytest
from google.adk.agents import LlmAgent
from google.adk.models import BaseLlm
from google.adk.models.llm_request import LlmRequest
from google.adk.models.llm_response import LlmResponse
from google.adk.sessions import InMemorySessionService
from google.genai import types
from pydantic import PrivateAttr, SecretStr

from app.core.ratelimit import Limiter
from app.models import Conversation, User
from app.services import chat


class StreamingLlm(BaseLlm):
    """Streams the chunks; "RAISE" fails and "HANG" stalls at that point."""

    _chunks: list[str] = PrivateAttr(default_factory=list)

    async def generate_content_async(
        self, llm_request: LlmRequest, stream: bool = False
    ) -> AsyncGenerator[LlmResponse]:
        text = ""
        for chunk in self._chunks:
            if chunk == "RAISE":
                raise RuntimeError("connection reset")
            if chunk == "HANG":
                await asyncio.sleep(30)
            text += chunk
            yield LlmResponse(
                content=types.Content(role="model", parts=[types.Part(text=chunk)]), partial=True
            )
        yield LlmResponse(
            content=types.Content(role="model", parts=[types.Part(text=text)]), turn_complete=True
        )


@pytest.fixture
def model(monkeypatch: pytest.MonkeyPatch) -> StreamingLlm:
    llm = StreamingLlm(model="scripted")
    monkeypatch.setattr(chat.settings, "OFFLINE_INTEGRATIONS", False)
    monkeypatch.setattr(chat.settings, "GEMINI_API_KEY", SecretStr("test"))
    monkeypatch.setattr(
        chat,
        "build_assistant",
        lambda *_, **__: LlmAgent(name="assistant", model=llm, instruction="Be brief."),
    )
    return llm


@pytest.fixture
def saved(monkeypatch: pytest.MonkeyPatch) -> list[dict[str, Any]]:
    records: list[dict[str, Any]] = []

    async def save(self: object, conversation: Conversation, turn: Any) -> uuid.UUID:
        records.append({"text": turn.text, "complete": turn.complete})
        return uuid.uuid4()

    monkeypatch.setattr(chat.ChatService, "_save", save)
    return records


def service() -> tuple[chat.ChatService, Conversation]:
    user = User(id=uuid.uuid4(), firebase_uid="u")
    conversation = Conversation(id=uuid.uuid4(), user_id=user.id)
    integrations: Any = None
    return (
        chat.ChatService(
            None, user, integrations, Limiter("async+memory://"), InMemorySessionService()
        ),  # type: ignore[arg-type]
        conversation,
    )


async def test_complete_reply_is_saved_once(model: StreamingLlm, saved: list[Any]) -> None:
    model._chunks = ["Hel", "lo"]
    chat_service, conversation = service()
    events = [e async for e in chat_service.reply(conversation, "hi")]
    assert [e.kind for e in events] == ["token", "token", "done"]
    assert saved == [{"text": "Hello", "complete": True}]


async def test_error_mid_stream_keeps_the_partial_reply(
    model: StreamingLlm, saved: list[Any]
) -> None:
    model._chunks = ["Hel", "RAISE"]
    chat_service, conversation = service()
    events = [e async for e in chat_service.reply(conversation, "hi")]
    assert [e.kind for e in events] == ["token", "error"]
    assert events[-1].data == {"error": "RuntimeError"}
    assert saved == [{"text": "Hel", "complete": False}]


async def test_client_leaving_keeps_the_partial_reply(
    model: StreamingLlm, saved: list[Any]
) -> None:
    model._chunks = ["Hel", "lo", "HANG"]
    chat_service, conversation = service()
    stream = chat_service.reply(conversation, "hi")
    assert (await anext(stream)).message == "Hel"
    await stream.aclose()
    assert saved == [{"text": "Hel", "complete": False}]


async def test_deadline_ends_the_turn_cleanly(
    model: StreamingLlm, saved: list[Any], monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setattr(chat.settings, "CHAT_DEADLINE_SECONDS", 0.3)
    model._chunks = ["Hel", "HANG"]
    chat_service, conversation = service()
    events = [e async for e in chat_service.reply(conversation, "hi")]
    assert [e.kind for e in events] == ["token", "error"]
    assert events[-1].data == {"error": "deadline"}
    assert saved == [{"text": "Hel", "complete": False}]


async def test_error_before_any_text_saves_nothing(model: StreamingLlm, saved: list[Any]) -> None:
    model._chunks = ["RAISE"]
    chat_service, conversation = service()
    events = [e async for e in chat_service.reply(conversation, "hi")]
    assert [e.kind for e in events] == ["error"]
    assert saved == []


def test_whitespace_only_message_is_rejected() -> None:
    from pydantic import ValidationError

    from app.schemas.content import ChatRequest

    assert ChatRequest(content="  Momo?  ").content == "Momo?"
    with pytest.raises(ValidationError):
        ChatRequest(content=" \n ")
