"""Fixtures for adapter tests: a fresh in-memory cache, no real waiting, one shared HTTP client."""

from collections.abc import AsyncIterator

import httpx
import pytest
from cashews import cache

from app.core.config import Settings
from app.integrations import http as http_module
from app.integrations.http import create_http_client


@pytest.fixture(autouse=True)
async def _memory_cache() -> AsyncIterator[None]:
    cache.setup("mem://")
    yield
    await cache.clear()


@pytest.fixture(autouse=True)
def _fresh_limiters(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(http_module, "_limiters", {})


@pytest.fixture
def sleeps(monkeypatch: pytest.MonkeyPatch) -> list[float]:
    """Records retry back-off waits instead of sleeping."""
    recorded: list[float] = []

    async def fake_sleep(seconds: float) -> None:
        recorded.append(seconds)

    monkeypatch.setattr(http_module, "_sleep", fake_sleep)
    return recorded


@pytest.fixture
def settings() -> Settings:
    return Settings(HTTP_USER_AGENT="Travya-tests/1.0 (+https://example.org/travya)")


@pytest.fixture
async def http(settings: Settings) -> AsyncIterator[httpx.AsyncClient]:
    async with create_http_client(settings) as client:
        yield client
