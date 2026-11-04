"""Gemini access: the ADK model with retries and a fallback model, plus embeddings.

With OFFLINE_INTEGRATIONS (tests, keyless demos) embeddings are deterministic hashes, and agents are
replaced by scripted fakes at the agent layer.
"""

import hashlib
import math
from collections.abc import AsyncGenerator, Sequence
from functools import lru_cache
from typing import Literal

from google.adk.models import Gemini
from google.adk.models.llm_request import LlmRequest
from google.adk.models.llm_response import LlmResponse
from google.genai import Client, errors, types

from app.core.config import settings
from app.core.errors import UpstreamUnavailable
from app.core.logging import get_logger

log = get_logger(__name__)

_RETRYABLE = {429, 500, 502, 503, 504}


def _api_key() -> str | None:
    return settings.GEMINI_API_KEY.get_secret_value() if settings.GEMINI_API_KEY else None


class FallbackGemini(Gemini):
    """Gemini that switches to a lighter model when the primary one is overloaded."""

    fallback_model: str | None = None

    async def generate_content_async(
        self, llm_request: LlmRequest, stream: bool = False
    ) -> AsyncGenerator[LlmResponse]:
        yielded = False
        try:
            async for response in super().generate_content_async(llm_request, stream):
                yielded = True
                yield response
        except errors.APIError as exc:
            if yielded or exc.code not in _RETRYABLE or not self.fallback_model:
                raise
            log.warning(
                "llm_fallback",
                primary=llm_request.model,
                fallback=self.fallback_model,
                code=exc.code,
            )
            llm_request.model = self.fallback_model
            async for response in super().generate_content_async(llm_request, stream):
                yield response


def agent_model() -> FallbackGemini:
    return FallbackGemini(
        model=settings.GEMINI_MODEL,
        fallback_model=settings.GEMINI_FALLBACK_MODEL,
        client_kwargs={"api_key": _api_key()},
        retry_options=types.HttpRetryOptions(
            attempts=3, initial_delay=1.0, max_delay=8.0, http_status_codes=[429, 503]
        ),
    )


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
def _client() -> Client:
    return Client(api_key=_api_key())


def _fake_embedding(text: str) -> list[float]:
    values: list[float] = []
    seed = text.lower().encode()
    while len(values) < settings.EMBEDDING_DIM:
        seed = hashlib.sha256(seed).digest()
        values.extend((b - 127.5) / 127.5 for b in seed)
    vector = values[: settings.EMBEDDING_DIM]
    norm = math.sqrt(sum(v * v for v in vector)) or 1.0
    return [v / norm for v in vector]


async def embed(
    texts: Sequence[str], *, task: Literal["RETRIEVAL_DOCUMENT", "RETRIEVAL_QUERY"]
) -> list[list[float]]:
    if not texts:
        return []
    if settings.OFFLINE_INTEGRATIONS or not _api_key():
        return [_fake_embedding(t) for t in texts]
    try:
        result = await _client().aio.models.embed_content(
            model=settings.GEMINI_EMBEDDING_MODEL,
            contents=list(texts),
            config=types.EmbedContentConfig(
                task_type=task, output_dimensionality=settings.EMBEDDING_DIM
            ),
        )
    except errors.APIError as exc:
        raise UpstreamUnavailable("The embedding service is busy, please retry") from exc
    vectors = [e.values or [] for e in result.embeddings or []]
    # Truncated Gemini embeddings must be re-normalised for cosine distance.
    out = []
    for vector in vectors:
        norm = math.sqrt(sum(v * v for v in vector)) or 1.0
        out.append([v / norm for v in vector])
    return out
