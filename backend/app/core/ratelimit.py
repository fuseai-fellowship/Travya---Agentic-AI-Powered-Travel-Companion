"""Per-user rate limits and the global daily LLM budget, on the `limits` library.

Backed by Redis when REDIS_URL is set (Upstash in production), in memory otherwise. When Redis
fails or stalls, limits fall back to this process's memory: a Redis blip must not turn every
request into a 500.
"""

import asyncio
import time
from collections.abc import Awaitable, Callable

from limits import RateLimitItem, parse
from limits.aio.strategies import FixedWindowRateLimiter, MovingWindowRateLimiter
from limits.errors import StorageError
from limits.storage import storage_from_string

from app.core.config import settings
from app.core.errors import BudgetExhausted, RateLimited
from app.core.logging import get_logger

log = get_logger(__name__)

STORAGE_TIMEOUT_S = 2.0
BUDGET_MESSAGE = (
    "The free demo has used today's AI quota. It resets daily; "
    "cached example trips are still available."
)
# A plan takes three to six model calls and a chat turn one to three; used to show runs left.
CALLS_PER_RUN = 4


def _storage_uri() -> str:
    if settings.REDIS_URL:
        return f"async+{settings.REDIS_URL}"
    return "async+memory://"


class _Windows:
    def __init__(self, uri: str) -> None:
        storage = storage_from_string(uri, wrap_exceptions=True)
        self.moving = MovingWindowRateLimiter(storage)
        self.fixed = FixedWindowRateLimiter(storage)

    async def hit(self, item: RateLimitItem, scope: str, key: str) -> float | None:
        """None when allowed, else when the window resets (epoch seconds)."""
        if await self.moving.hit(item, scope, key):
            return None
        return (await self.moving.get_window_stats(item, scope, key)).reset_time


class Limiter:
    def __init__(self, uri: str | None = None) -> None:
        self._shared = _Windows(uri or _storage_uri())
        self._local = _Windows("async+memory://")
        self._degraded = False

    async def _run[T](self, operation: Callable[[_Windows], Awaitable[T]]) -> T:
        try:
            async with asyncio.timeout(STORAGE_TIMEOUT_S):
                result = await operation(self._shared)
        except (StorageError, TimeoutError) as exc:
            if not self._degraded:
                log.error("rate_limit_storage_unavailable", error=type(exc).__name__)
                self._degraded = True
            return await operation(self._local)
        if self._degraded:
            log.info("rate_limit_storage_recovered")
            self._degraded = False
        return result

    async def hit(self, limit: str, scope: str, key: str) -> None:
        item = parse(limit)
        reset = await self._run(lambda windows: windows.hit(item, scope, key))
        if reset is not None:
            raise RateLimited(
                f"Rate limit reached ({limit}). Try again later.",
                retry_after=max(1, int(reset - time.time())),
            )

    async def spend_llm_budget(self) -> None:
        """One unit per model call, shared by all users, reset daily."""
        item = parse(f"{settings.LLM_DAILY_REQUEST_BUDGET}/day")
        if not await self._run(lambda windows: windows.fixed.hit(item, "llm-budget", "global")):
            raise BudgetExhausted(BUDGET_MESSAGE)

    async def check_llm_budget(self) -> None:
        """Refuse to start a run when nothing is left, before a stream opens."""
        if await self.remaining_llm_budget() <= 0:
            raise BudgetExhausted(BUDGET_MESSAGE)

    async def remaining_llm_budget(self) -> int:
        item = parse(f"{settings.LLM_DAILY_REQUEST_BUDGET}/day")
        stats = await self._run(
            lambda windows: windows.fixed.get_window_stats(item, "llm-budget", "global")
        )
        return int(stats.remaining)
