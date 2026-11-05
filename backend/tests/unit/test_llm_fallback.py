"""Model chain and key failover for Gemini, without network."""

from collections.abc import AsyncGenerator
from typing import Any

import pytest
from google.genai import errors

from app.core.errors import UpstreamUnavailable
from app.llm import client
from app.llm.client import FallbackGemini


def api_error(code: int, message: str = "x") -> errors.APIError:
    cls = errors.ClientError if code < 500 else errors.ServerError
    return cls(code, {"error": {"code": code, "message": message, "status": "X"}})


class FakeDelegate:
    def __init__(self, outcome: Any, calls: list[str], label: str) -> None:
        self.outcome, self.calls, self.label = outcome, calls, label

    async def generate_content_async(
        self, request: Any, stream: bool = False
    ) -> AsyncGenerator[str]:
        self.calls.append(self.label)
        if isinstance(self.outcome, Exception):
            raise self.outcome
        yield self.outcome


@pytest.fixture
def keys(monkeypatch: pytest.MonkeyPatch) -> None:
    from pydantic import SecretStr

    monkeypatch.setattr(client.settings, "GEMINI_API_KEY", SecretStr("k0"))
    monkeypatch.setattr(client.settings, "GEMINI_BACKUP_API_KEYS", SecretStr("k1,k2"))
    monkeypatch.setattr(client, "KEYS", client._KeyPool())


def chain(outcomes: dict[tuple[str, str], Any], calls: list[str]) -> FallbackGemini:
    llm = FallbackGemini.chain(
        ["primary", "lite", "older"], client.types.HttpRetryOptions(attempts=1)
    )
    llm._delegate = lambda model, index, key: FakeDelegate(  # type: ignore[method-assign]
        outcomes.get((model, key), "ok"), calls, f"{model}/{key}"
    )
    return llm


async def collect(llm: FallbackGemini) -> list[Any]:
    request = type("Request", (), {"model": None})()
    return [r async for r in llm.generate_content_async(request)]  # type: ignore[arg-type]


async def test_overloaded_model_falls_back_to_next_model(keys: None) -> None:
    calls: list[str] = []
    llm = chain({("primary", "k0"): api_error(503), ("lite", "k0"): api_error(504)}, calls)
    assert await collect(llm) == ["ok"]
    assert calls == ["primary/k0", "lite/k0", "older/k0"]


async def test_revoked_key_moves_to_next_key_and_stays_disabled(keys: None) -> None:
    calls: list[str] = []
    llm = chain({("primary", "k0"): api_error(403, "PERMISSION_DENIED")}, calls)
    assert await collect(llm) == ["ok"]
    assert await collect(llm) == ["ok"]
    assert calls == ["primary/k0", "primary/k1", "primary/k1"]


async def test_quota_does_not_rotate_keys(keys: None) -> None:
    calls: list[str] = []
    llm = chain({(m, "k0"): api_error(429) for m in ("primary", "lite", "older")}, calls)
    with pytest.raises(errors.ClientError):
        await collect(llm)
    assert all(call.endswith("/k0") for call in calls)


async def test_client_errors_are_not_retried(keys: None) -> None:
    calls: list[str] = []
    llm = chain({("primary", "k0"): api_error(400, "bad schema")}, calls)
    with pytest.raises(errors.ClientError):
        await collect(llm)
    assert calls == ["primary/k0"]


async def test_no_working_key_is_a_clear_error(keys: None) -> None:
    calls: list[str] = []
    bad = {("primary", k): api_error(401) for k in ("k0", "k1", "k2")}
    with pytest.raises(UpstreamUnavailable, match="No working Gemini API key"):
        await collect(chain(bad, calls))


def test_settings_key_list_and_models(monkeypatch: pytest.MonkeyPatch) -> None:
    from pydantic import SecretStr

    from app.core.config import Settings

    s = Settings(
        _env_file=None,  # type: ignore[call-arg]
        GEMINI_API_KEY=SecretStr("a"),
        GEMINI_BACKUP_API_KEYS=SecretStr(" b, a ,,c "),
        GEMINI_FALLBACK_MODELS="x, y",
    )
    assert s.gemini_api_keys() == ["a", "b", "c"]
    assert s.gemini_fallback_models() == ["x", "y"]
