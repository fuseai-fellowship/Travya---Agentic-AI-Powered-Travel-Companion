"""Per-user rate limits and the global daily LLM budget, on the `limits` library.

Backed by Redis when REDIS_URL is set (Upstash in production), in memory otherwise.
"""

import time

from limits import parse
from limits.aio.strategies import FixedWindowRateLimiter, MovingWindowRateLimiter
from limits.storage import storage_from_string

from app.core.config import settings
from app.core.errors import BudgetExhausted, RateLimited


def _storage_uri() -> str:
    if settings.REDIS_URL:
        return f"async+{settings.REDIS_URL}"
    return "async+memory://"


class Limiter:
    def __init__(self, uri: str | None = None) -> None:
        storage = storage_from_string(uri or _storage_uri())
        self._moving = MovingWindowRateLimiter(storage)
        self._fixed = FixedWindowRateLimiter(storage)

    async def hit(self, limit: str, scope: str, key: str) -> None:
        item = parse(limit)
        if await self._moving.hit(item, scope, key):
            return
        stats = await self._moving.get_window_stats(item, scope, key)
        raise RateLimited(
            f"Rate limit reached ({limit}). Try again later.",
            retry_after=max(1, int(stats.reset_time - time.time())),
        )

    async def spend_llm_budget(self) -> None:
        """One unit per agent run, shared by all users, reset daily."""
        item = parse(f"{settings.LLM_DAILY_REQUEST_BUDGET}/day")
        if not await self._fixed.hit(item, "llm-budget", "global"):
            raise BudgetExhausted(
                "The free demo has used today's AI quota. It resets daily; cached example trips are still available."
            )

    async def remaining_llm_budget(self) -> int:
        item = parse(f"{settings.LLM_DAILY_REQUEST_BUDGET}/day")
        stats = await self._fixed.get_window_stats(item, "llm-budget", "global")
        return int(stats.remaining)
