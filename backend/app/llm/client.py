"""Gemini access: the ADK model over a chain of fallback models and keys, plus embeddings.

With OFFLINE_INTEGRATIONS (tests, keyless demos) embeddings are deterministic hashes, and agents are
replaced by scripted fakes at the agent layer.
"""

import hashlib
import math
from collections.abc import AsyncGenerator, Sequence
from functools import lru_cache
from typing import Literal

import httpx
from google.adk.models import Gemini
from google.adk.models.llm_request import LlmRequest
from google.adk.models.llm_response import LlmResponse
from google.genai import Client, errors, types
from pydantic import PrivateAttr

from app.core.config import settings
from app.core.errors import UpstreamUnavailable
from app.core.logging import get_logger

log = get_logger(__name__)

_OVERLOADED = {429, 500, 502, 503, 504}


def _is_bad_key(exc: Exception) -> bool:
    """Revoked, disabled or malformed key: another key may work; another model would not."""
    if not isinstance(exc, errors.ClientError):
        return False
    return exc.code in (401, 403) or (exc.code == 400 and "API key" in str(exc))


class _KeyPool:
    """Gemini keys in priority order; a key that fails authentication is skipped from then on."""

    def __init__(self) -> None:
        self._disabled: set[int] = set()

    def active(self) -> list[tuple[int, str]]:
        return [(i, k) for i, k in enumerate(settings.gemini_api_keys()) if i not in self._disabled]

    def first(self) -> tuple[int, str]:
        keys = self.active()
        if not keys:
            raise UpstreamUnavailable("No working Gemini API key is configured")
        return keys[0]

    def disable(self, index: int, exc: Exception) -> None:
        self._disabled.add(index)
        code = getattr(exc, "code", None)
        log.error("gemini_key_disabled", key_index=index, code=code, remaining=len(self.active()))


KEYS = _KeyPool()


class FallbackGemini(Gemini):
    """Gemini over a chain of models and keys.

    Overload (503/504, 429, timeouts) moves to the next model; an authentication failure moves to the
    next key with the same model. Nothing is retried once a response has started streaming.
    """

    _models: list[str] = PrivateAttr(default_factory=list)
    _delegates: dict[tuple[str, int], Gemini] = PrivateAttr(default_factory=dict)

    @classmethod
    def chain(cls, models: list[str], retry: types.HttpRetryOptions) -> "FallbackGemini":
        llm = cls(model=models[0], retry_options=retry)
        llm._models = models
        return llm

    def _delegate(self, model: str, index: int, key: str) -> Gemini:
        if (model, index) not in self._delegates:
            self._delegates[model, index] = Gemini(
                model=model, client_kwargs={"api_key": key}, retry_options=self.retry_options
            )
        return self._delegates[model, index]

    async def generate_content_async(
        self, llm_request: LlmRequest, stream: bool = False
    ) -> AsyncGenerator[LlmResponse]:
        failure: Exception | None = None
        for model in self._models or [self.model]:
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
                    return
                except (errors.APIError, httpx.TimeoutException) as exc:
                    if started:
                        raise
                    if _is_bad_key(exc):
                        KEYS.disable(index, exc)
                        continue  # same model, next key
                    code = exc.code if isinstance(exc, errors.APIError) else 504
                    if code not in _OVERLOADED:
                        raise
                    log.warning("llm_fallback", model=model, code=code)
                    failure = exc
                    break  # next model
        assert failure is not None
        raise failure


def agent_model(*, light: bool = False) -> FallbackGemini:
    """The main model followed by the fallbacks, or the fallbacks alone for light tasks."""
    fallbacks = settings.gemini_fallback_models()
    models = fallbacks if light and fallbacks else [settings.GEMINI_MODEL, *fallbacks]
    return FallbackGemini.chain(
        list(dict.fromkeys(models)),
        types.HttpRetryOptions(
            attempts=2, initial_delay=1.0, max_delay=4.0, http_status_codes=[500, 502]
        ),
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
    return Client(api_key=key)


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
        except errors.APIError as exc:
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
