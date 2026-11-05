"""Gemini access: the ADK model over a chain of fallback models and keys, plus embeddings.

With OFFLINE_INTEGRATIONS (tests, keyless demos) embeddings are deterministic hashes, and agents are
replaced by scripted fakes at the agent layer.
"""

import hashlib
import math
import time
from collections.abc import AsyncGenerator, Awaitable, Callable, Sequence
from functools import lru_cache
from typing import Literal

import httpx
from google.adk.models import Gemini
from google.adk.models.llm_request import LlmRequest
from google.adk.models.llm_response import LlmResponse
from google.genai import Client, errors, types
from pydantic import PrivateAttr

from app.core.config import settings
from app.core.errors import BudgetExhausted, UpstreamUnavailable
from app.core.logging import get_logger

log = get_logger(__name__)

EMBED_TIMEOUT_S = 20.0
QUOTA_MESSAGE = (
    "The free demo's AI models are at their usage limit right now. "
    "Try again in a minute; the daily quota resets at midnight Pacific time."
)

_OVERLOADED = {500, 502, 503, 504}
# google.rpc.ErrorInfo reasons (and message fragments) that mean the key itself is unusable:
# another key may work, another model would not.
_KEY_REASONS = {
    "API_KEY_INVALID",
    "API_KEY_EXPIRED",
    "API_KEY_SERVICE_BLOCKED",
    "API_KEY_HTTP_REFERRER_BLOCKED",
    "API_KEY_IP_ADDRESS_BLOCKED",
    "CONSUMER_SUSPENDED",
    "SERVICE_DISABLED",  # the API is off in the key's project; another project's key may work
}
_KEY_MESSAGES = ("api key not valid", "api key expired", "reported as leaked", "has been suspended")
KEY_COOLDOWN_S = 600.0
BREAKER_FAILURES = 3
BREAKER_COOLDOWN_S = 60.0


def _reasons(exc: errors.APIError) -> set[str]:
    error = exc.details.get("error") if isinstance(exc.details, dict) else None
    details = error.get("details") if isinstance(error, dict) else None
    return {d["reason"] for d in details or [] if isinstance(d, dict) and d.get("reason")}


def _is_bad_key(exc: Exception) -> bool:
    """Invalid, expired, leaked, blocked or suspended key. A model-scoped 403 is not one."""
    if not isinstance(exc, errors.ClientError):
        return False
    if exc.code == 401 or _reasons(exc) & _KEY_REASONS:
        return True
    message = (exc.message or "").lower()
    return exc.code in (400, 403) and any(m in message for m in _KEY_MESSAGES)


def _is_quota(exc: Exception) -> bool:
    return isinstance(exc, errors.ClientError) and exc.code == 429


def _is_unavailable_model(exc: Exception) -> bool:
    """Retired or renamed (404), or not enabled for this project (403)."""
    return isinstance(exc, errors.ClientError) and exc.code in (403, 404)


def _code(exc: Exception) -> int:
    return exc.code if isinstance(exc, errors.APIError) else 504


class _KeyPool:
    """Gemini keys in priority order. A key that fails for key-level reasons is skipped for a
    cool-down, never because of quota: rotating keys around rate limits breaks Google's terms."""

    def __init__(self) -> None:
        self._disabled_until: dict[int, float] = {}

    def active(self) -> list[tuple[int, str]]:
        now = time.monotonic()
        return [
            (i, k)
            for i, k in enumerate(settings.gemini_api_keys())
            if self._disabled_until.get(i, 0.0) <= now
        ]

    def first(self) -> tuple[int, str]:
        keys = self.active()
        if not keys:
            raise UpstreamUnavailable("No working Gemini API key is configured")
        return keys[0]

    def disable(self, index: int, exc: Exception) -> None:
        self._disabled_until[index] = time.monotonic() + KEY_COOLDOWN_S
        reasons = sorted(_reasons(exc)) if isinstance(exc, errors.APIError) else []
        log.error(
            "gemini_key_disabled",
            key_index=index,
            code=getattr(exc, "code", None),
            reasons=reasons,
            remaining=len(self.active()),
            cooldown_s=KEY_COOLDOWN_S,
        )


class _Breaker:
    """Moves a model to the back of the chain for a while after repeated overloads or timeouts,
    so every call does not first wait on a model that keeps failing."""

    def __init__(self) -> None:
        self._failures: dict[str, int] = {}
        self._open_until: dict[str, float] = {}

    def is_open(self, model: str) -> bool:
        return self._open_until.get(model, 0.0) > time.monotonic()

    def order(self, models: list[str]) -> list[str]:
        return sorted(models, key=self.is_open)  # stable: the configured order otherwise

    def failure(self, model: str) -> None:
        self._failures[model] = self._failures.get(model, 0) + 1
        if self._failures[model] >= BREAKER_FAILURES:
            self._failures[model] = 0
            self._open_until[model] = time.monotonic() + BREAKER_COOLDOWN_S
            log.warning("llm_model_paused", model=model, seconds=BREAKER_COOLDOWN_S)

    def success(self, model: str) -> None:
        self._failures.pop(model, None)


KEYS = _KeyPool()
BREAKER = _Breaker()
# Shared across requests so each (model, key) keeps one client and its connection pool.
_DELEGATES: dict[tuple[str, str, str], Gemini] = {}


class FallbackGemini(Gemini):
    """Gemini over a chain of models and keys.

    Overload (500/502/503/504, timeouts), quota (429) and an unavailable model (403/404) move to
    the next model; a key-level failure moves to the next key with the same model. Nothing is
    retried once a response has started streaming. When every model is out of quota the demo's
    budget is reported as exhausted.
    """

    _models: list[str] = PrivateAttr(default_factory=list)
    _budget: Callable[[], Awaitable[None]] | None = PrivateAttr(default=None)

    @classmethod
    def chain(
        cls,
        models: list[str],
        retry: types.HttpRetryOptions,
        budget: Callable[[], Awaitable[None]] | None = None,
    ) -> "FallbackGemini":
        llm = cls(model=models[0], retry_options=retry)
        llm._models = models
        llm._budget = budget
        return llm

    def _delegate(self, model: str, index: int, key: str) -> Gemini:
        retry = self.retry_options.model_dump_json() if self.retry_options else ""
        cache_key = (model, key, retry)
        if cache_key not in _DELEGATES:
            _DELEGATES[cache_key] = Gemini(
                model=model, client_kwargs={"api_key": key}, retry_options=self.retry_options
            )
        return _DELEGATES[cache_key]

    async def generate_content_async(
        self, llm_request: LlmRequest, stream: bool = False
    ) -> AsyncGenerator[LlmResponse]:
        if self._budget is not None:
            await self._budget()  # one unit per model call, whichever model answers
        failures: list[Exception] = []
        for model in BREAKER.order(self._models or [self.model]):
            while True:
                index, key = KEYS.first()
                llm_request.model = model
                started = False
                try:
                    async for response in self._delegate(model, index, key).generate_content_async(
                        llm_request, stream
                    ):
                        started = True
                        yield response
                    BREAKER.success(model)
                    return
                except (errors.APIError, httpx.TimeoutException) as exc:
                    if started:
                        raise
                    if _is_bad_key(exc):
                        KEYS.disable(index, exc)
                        continue  # same model, next key
                    if _is_quota(exc):
                        log.warning("llm_quota", model=model)
                    elif _is_unavailable_model(exc):
                        log.error("llm_model_unavailable", model=model, code=_code(exc))
                    elif _code(exc) in _OVERLOADED:
                        BREAKER.failure(model)
                        log.warning("llm_fallback", model=model, code=_code(exc))
                    else:
                        raise
                    failures.append(exc)
                    break  # next model
        if failures and all(_is_quota(f) for f in failures):
            raise BudgetExhausted(QUOTA_MESSAGE) from failures[-1]
        raise failures[-1]


def agent_model(
    *, light: bool = False, budget: Callable[[], Awaitable[None]] | None = None
) -> FallbackGemini:
    """The main model followed by the fallbacks, or the fallbacks alone for light tasks.

    `budget` is awaited before every model call and raises BudgetExhausted when the day's
    budget is spent.
    """
    fallbacks = settings.gemini_fallback_models()
    models = fallbacks if light and fallbacks else [settings.GEMINI_MODEL, *fallbacks]
    return FallbackGemini.chain(
        list(dict.fromkeys(models)),
        types.HttpRetryOptions(
            attempts=2, initial_delay=1.0, max_delay=4.0, http_status_codes=[500, 502]
        ),
        budget,
    )


def http_options(timeout_s: float) -> types.HttpOptions:
    return types.HttpOptions(timeout=int(timeout_s * 1000))


SAFETY_SETTINGS = [
    types.SafetySetting(
        category=category, threshold=types.HarmBlockThreshold.BLOCK_MEDIUM_AND_ABOVE
    )
    for category in (
        types.HarmCategory.HARM_CATEGORY_HARASSMENT,
        types.HarmCategory.HARM_CATEGORY_HATE_SPEECH,
        types.HarmCategory.HARM_CATEGORY_SEXUALLY_EXPLICIT,
        types.HarmCategory.HARM_CATEGORY_DANGEROUS_CONTENT,
    )
]


@lru_cache
def _client(key: str) -> Client:
    return Client(api_key=key, http_options=http_options(EMBED_TIMEOUT_S))


def _fake_embedding(text: str) -> list[float]:
    values: list[float] = []
    seed = text.lower().encode()
    while len(values) < settings.EMBEDDING_DIM:
        seed = hashlib.sha256(seed).digest()
        values.extend((b - 127.5) / 127.5 for b in seed)
    vector = values[: settings.EMBEDDING_DIM]
    norm = math.sqrt(sum(v * v for v in vector)) or 1.0
    return [v / norm for v in vector]


async def _embed_batch(
    texts: list[str], task: Literal["RETRIEVAL_DOCUMENT", "RETRIEVAL_QUERY"]
) -> list[list[float]]:
    while True:
        index, key = KEYS.first()
        try:
            result = await _client(key).aio.models.embed_content(
                model=settings.GEMINI_EMBEDDING_MODEL,
                contents=texts,
                config=types.EmbedContentConfig(
                    task_type=task, output_dimensionality=settings.EMBEDDING_DIM
                ),
            )
        except (errors.APIError, httpx.TimeoutException) as exc:
            if _is_bad_key(exc):
                KEYS.disable(index, exc)
                continue
            raise UpstreamUnavailable("The embedding service is busy, please retry") from exc
        return [e.values or [] for e in result.embeddings or []]


async def embed(
    texts: Sequence[str], *, task: Literal["RETRIEVAL_DOCUMENT", "RETRIEVAL_QUERY"]
) -> list[list[float]]:
    if not texts:
        return []
    if settings.OFFLINE_INTEGRATIONS or not settings.gemini_api_keys():
        return [_fake_embedding(t) for t in texts]
    vectors = await _embed_batch(list(texts), task)
    if len(vectors) != len(texts):
        # Multimodal embedding models merge a list of inputs into one vector; embed one by one.
        vectors = [v for text in texts for v in await _embed_batch([text], task)]
    # Truncated Gemini embeddings must be re-normalised for cosine distance.
    out = []
    for vector in vectors:
        norm = math.sqrt(sum(v * v for v in vector)) or 1.0
        out.append([v / norm for v in vector])
    return out
