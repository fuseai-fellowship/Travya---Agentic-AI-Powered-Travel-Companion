"""Model chain and key failover for Gemini, without network."""

from collections.abc import AsyncGenerator
from typing import Any

import pytest
from google.genai import errors

from app.core.errors import BudgetExhausted, UpstreamUnavailable
from app.llm import client
from app.llm.client import FallbackGemini


def api_error(code: int, message: str = "x", reason: str | None = None) -> errors.APIError:
    cls = errors.ClientError if code < 500 else errors.ServerError
    details = [{"@type": "type.googleapis.com/google.rpc.ErrorInfo", "reason": reason}]
    error = {"code": code, "message": message, "status": "X", "details": details if reason else []}
    return cls(code, {"error": error})


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
    monkeypatch.setattr(client, "BREAKER", client._Breaker())


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


@pytest.mark.parametrize(
    "error",
    [
        api_error(400, "API key not valid. Please pass a valid API key.", "API_KEY_INVALID"),
        api_error(403, "Your API key was reported as leaked.", None),
        api_error(403, "Requests are blocked.", "API_KEY_SERVICE_BLOCKED"),
        api_error(401, "Unauthenticated"),
    ],
)
async def test_bad_key_moves_to_next_key_for_a_cool_down(
    keys: None, monkeypatch: pytest.MonkeyPatch, error: errors.APIError
) -> None:
    calls: list[str] = []
    llm = chain({("primary", "k0"): error}, calls)
    assert await collect(llm) == ["ok"]
    assert await collect(llm) == ["ok"]
    assert calls == ["primary/k0", "primary/k1", "primary/k1"]
    # After the cool-down the primary key is tried again.
    now = client.time.monotonic()
    monkeypatch.setattr(client.time, "monotonic", lambda: now + client.KEY_COOLDOWN_S + 1)
    assert client.KEYS.first() == (0, "k0")


async def test_model_scoped_403_and_404_move_to_the_next_model(keys: None) -> None:
    calls: list[str] = []
    llm = chain(
        {
            ("primary", "k0"): api_error(403, "Permission denied on this model"),
            ("lite", "k0"): api_error(404, "models/lite is not found"),
        },
        calls,
    )
    assert await collect(llm) == ["ok"]
    assert calls == ["primary/k0", "lite/k0", "older/k0"]
    assert client.KEYS.active() == [(0, "k0"), (1, "k1"), (2, "k2")]


async def test_quota_does_not_rotate_keys(keys: None) -> None:
    calls: list[str] = []
    llm = chain({(m, "k0"): api_error(429) for m in ("primary", "lite", "older")}, calls)
    with pytest.raises(BudgetExhausted):
        await collect(llm)
    assert calls == ["primary/k0", "lite/k0", "older/k0"]


async def test_quota_on_one_model_falls_back_to_the_next(keys: None) -> None:
    calls: list[str] = []
    llm = chain({("primary", "k0"): api_error(429)}, calls)
    assert await collect(llm) == ["ok"]
    assert calls == ["primary/k0", "lite/k0"]


async def test_repeatedly_overloaded_model_is_tried_last_for_a_while(
    keys: None, monkeypatch: pytest.MonkeyPatch
) -> None:
    calls: list[str] = []
    llm = chain({("primary", "k0"): api_error(503)}, calls)
    for _ in range(client.BREAKER_FAILURES):
        assert await collect(llm) == ["ok"]
    calls.clear()
    assert await collect(llm) == ["ok"]
    assert calls == ["lite/k0"]
    now = client.time.monotonic()
    monkeypatch.setattr(client.time, "monotonic", lambda: now + client.BREAKER_COOLDOWN_S + 1)
    calls.clear()
    await collect(llm)
    assert calls == ["primary/k0", "lite/k0"]


async def test_error_after_streaming_started_is_not_retried(keys: None) -> None:
    calls: list[str] = []

    class Broken(FakeDelegate):
        async def generate_content_async(
            self, request: Any, stream: bool = False
        ) -> AsyncGenerator[str]:
            self.calls.append(self.label)
            yield "partial"
            raise api_error(503)

    llm = FallbackGemini.chain(["primary", "lite"], client.types.HttpRetryOptions(attempts=1))
    llm._delegate = lambda model, index, key: Broken(None, calls, f"{model}/{key}")  # type: ignore[method-assign]
    received: list[Any] = []

    async def consume() -> None:
        request: Any = type("R", (), {"model": None})()
        async for response in llm.generate_content_async(request):
            received.append(response)

    with pytest.raises(errors.ServerError):
        await consume()
    assert received == ["partial"]
    assert calls == ["primary/k0"]


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


async def test_budget_is_spent_once_per_model_call(keys: None) -> None:
    calls: list[str] = []
    spent: list[int] = []

    async def budget() -> None:
        spent.append(1)

    llm = chain({("primary", "k0"): api_error(503)}, calls)
    llm._budget = budget
    assert await collect(llm) == ["ok"]
    assert calls == ["primary/k0", "lite/k0"]
    assert spent == [1]


async def test_exhausted_budget_stops_before_any_request(keys: None) -> None:
    calls: list[str] = []

    async def budget() -> None:
        raise BudgetExhausted("spent")

    llm = chain({}, calls)
    llm._budget = budget
    with pytest.raises(BudgetExhausted):
        await collect(llm)
    assert calls == []
