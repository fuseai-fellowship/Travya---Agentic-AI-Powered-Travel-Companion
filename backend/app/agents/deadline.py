"""An overall deadline for an agent run that streams its events."""

import asyncio
from collections.abc import AsyncGenerator, AsyncIterator


async def until[T](events: AsyncIterator[T], deadline: float) -> AsyncGenerator[T]:
    """Yields from `events` until the event loop's clock reaches `deadline`, then raises
    TimeoutError. The timeout wraps each wait, never a `yield`, so the consumer's own work
    between events cannot be cancelled by it."""
    while True:
        try:
            async with asyncio.timeout_at(deadline):
                item = await anext(events)
        except StopAsyncIteration:
            return
        yield item


def deadline_in(seconds: float) -> float:
    return asyncio.get_running_loop().time() + seconds
