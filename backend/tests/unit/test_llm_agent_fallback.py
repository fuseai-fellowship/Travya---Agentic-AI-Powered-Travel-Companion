"""FallbackGemini inside a real LlmAgent, with the Gemini REST API mocked at the HTTP layer."""

import json
from collections.abc import AsyncIterator
from typing import Any

import httpx
import pytest
import respx
from google.adk.agents import LlmAgent
from google.adk.agents.run_config import RunConfig, StreamingMode  # type: ignore[attr-defined]
from google.adk.runners import Runner
from google.adk.sessions import InMemorySessionService
from google.genai import types
from pydantic import SecretStr

from app.llm import client
from app.llm.client import FallbackGemini, http_options

API = "https://generativelanguage.googleapis.com/v1beta/models"


def reply(text: str) -> dict[str, Any]:
    return {
        "candidates": [
            {"content": {"role": "model", "parts": [{"text": text}]}, "finishReason": "STOP"}
        ]
    }


def error(code: int, status: str, message: str = "x") -> httpx.Response:
    return httpx.Response(
        code, json={"error": {"code": code, "status": status, "message": message}}
    )


@pytest.fixture(autouse=True)
def keys(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(client.settings, "GEMINI_API_KEY", SecretStr("k0"))
    monkeypatch.setattr(client.settings, "GEMINI_BACKUP_API_KEYS", SecretStr("k1"))
    monkeypatch.setattr(client, "KEYS", client._KeyPool())
    monkeypatch.setattr(client, "BREAKER", client._Breaker())
    monkeypatch.setattr(client, "_DELEGATES", {})


async def ask(streaming: bool = False) -> str:
    agent = LlmAgent(
        name="assistant",
        model=FallbackGemini.chain(
            ["primary", "lite", "older"], types.HttpRetryOptions(attempts=1)
        ),
        instruction="Be brief.",
        generate_content_config=types.GenerateContentConfig(http_options=http_options(5)),
    )
    sessions = InMemorySessionService()
    runner = Runner(app_name="t", agent=agent, session_service=sessions)
    session = await sessions.create_session(app_name="t", user_id="u")
    text = ""
    config = RunConfig(streaming_mode=StreamingMode.SSE if streaming else StreamingMode.NONE)
    async for event in runner.run_async(
        user_id="u",
        session_id=session.id,
        new_message=types.Content(role="user", parts=[types.Part(text="hi")]),
        run_config=config,
    ):
        if event.content and event.content.parts and (event.partial or not streaming):
            text += "".join(p.text or "" for p in event.content.parts)
    return text


@respx.mock
async def test_overload_retired_model_then_success() -> None:
    primary = respx.post(f"{API}/primary:generateContent").mock(
        return_value=error(503, "UNAVAILABLE")
    )
    lite = respx.post(f"{API}/lite:generateContent").mock(
        return_value=error(404, "NOT_FOUND", "models/lite is not found")
    )
    older = respx.post(f"{API}/older:generateContent").mock(
        return_value=httpx.Response(200, json=reply("hello"))
    )
    assert await ask() == "hello"
    assert (primary.call_count, lite.call_count, older.call_count) == (1, 1, 1)
    assert older.calls.last.request.headers["x-goog-api-key"] == "k0"


@respx.mock
async def test_model_scoped_403_keeps_the_key_and_timeout_falls_back() -> None:
    respx.post(f"{API}/primary:generateContent").mock(
        return_value=error(403, "PERMISSION_DENIED", "Model not enabled for this project")
    )
    respx.post(f"{API}/lite:generateContent").mock(side_effect=httpx.ReadTimeout("slow"))
    older = respx.post(f"{API}/older:generateContent").mock(
        return_value=httpx.Response(200, json=reply("ok"))
    )
    assert await ask() == "ok"
    assert older.calls.last.request.headers["x-goog-api-key"] == "k0"
    assert client.KEYS.first() == (0, "k0")


@respx.mock
async def test_invalid_key_moves_to_the_backup_key() -> None:
    def by_key(request: httpx.Request) -> httpx.Response:
        if request.headers["x-goog-api-key"] == "k0":
            body = {
                "error": {
                    "code": 400,
                    "status": "INVALID_ARGUMENT",
                    "message": "API key not valid. Please pass a valid API key.",
                    "details": [
                        {
                            "@type": "type.googleapis.com/google.rpc.ErrorInfo",
                            "reason": "API_KEY_INVALID",
                        }
                    ],
                }
            }
            return httpx.Response(400, json=body)
        return httpx.Response(200, json=reply("from k1"))

    respx.post(f"{API}/primary:generateContent").mock(side_effect=by_key)
    assert await ask() == "from k1"


class _BreaksAfterFirstChunk(httpx.AsyncByteStream):
    async def __aiter__(self) -> AsyncIterator[bytes]:
        yield f"data: {json.dumps(reply('Hel'))}\r\n\r\n".encode()
        raise httpx.ReadError("connection reset")


@respx.mock
async def test_stream_error_after_first_chunk_is_not_retried() -> None:
    primary = respx.post(url__regex=rf"{API}/primary:streamGenerateContent.*").mock(
        return_value=httpx.Response(
            200, headers={"content-type": "text/event-stream"}, stream=_BreaksAfterFirstChunk()
        )
    )
    lite = respx.post(url__regex=rf"{API}/lite:streamGenerateContent.*").mock(
        return_value=httpx.Response(200, json=reply("never"))
    )
    with pytest.raises(httpx.ReadError):
        await ask(streaming=True)
    assert (primary.call_count, lite.call_count) == (1, 0)
