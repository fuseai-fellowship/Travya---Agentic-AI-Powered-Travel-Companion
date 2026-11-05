"""Outbound HTTP: one shared client, polite per-host rate limits and retries with backoff."""

import asyncio
from collections.abc import Mapping
from contextlib import AbstractAsyncContextManager, nullcontext
from datetime import UTC, datetime
from email.utils import parsedate_to_datetime
from typing import Any

import httpx
from aiolimiter import AsyncLimiter
from tenacity import (
    AsyncRetrying,
    RetryCallState,
    retry_if_exception_type,
    retry_if_result,
    stop_after_attempt,
    wait_exponential_jitter,
)

from app.core.config import Settings
from app.core.errors import UpstreamUnavailable
from app.core.logging import get_logger

log = get_logger(__name__)

MAX_ATTEMPTS = 3
MAX_RETRY_AFTER_S = 10.0
RETRY_STATUSES = frozenset({429, 502, 503, 504})
RETRY_EXCEPTIONS = (
    httpx.ConnectError,
    httpx.ConnectTimeout,
    httpx.ReadError,
    httpx.ReadTimeout,
    httpx.RemoteProtocolError,
)
# (requests, per seconds) for hosts whose usage policy sets a rate
HOST_RATE_LIMITS: dict[str, tuple[float, float]] = {"nominatim.openstreetmap.org": (1, 1)}

_backoff = wait_exponential_jitter(initial=0.5, max=8, jitter=0.5)
_limiters: dict[str, AsyncLimiter] = {}
_sleep = asyncio.sleep


def create_http_client(settings: Settings) -> httpx.AsyncClient:
    """The one client shared by every adapter; the app closes it on shutdown."""
    return httpx.AsyncClient(
        headers={"User-Agent": settings.HTTP_USER_AGENT, "Accept": "application/json"},
        timeout=settings.HTTP_TIMEOUT_SECONDS,
        follow_redirects=True,
        http2=False,
    )


def host_limiter(host: str) -> AsyncLimiter | None:
    if host not in HOST_RATE_LIMITS:
        return None
    if host not in _limiters:
        _limiters[host] = AsyncLimiter(*HOST_RATE_LIMITS[host])
    return _limiters[host]


def retry_after_seconds(response: httpx.Response) -> float | None:
    """Retry-After (seconds or HTTP date), capped at MAX_RETRY_AFTER_S."""
    value = response.headers.get("Retry-After")
    if not value:
        return None
    try:
        seconds = float(value)
    except ValueError:
        try:
            seconds = (parsedate_to_datetime(value) - datetime.now(UTC)).total_seconds()
        except (TypeError, ValueError):
            return None
    return min(max(seconds, 0.0), MAX_RETRY_AFTER_S)


def _is_retryable(response: httpx.Response | None) -> bool:
    return response is not None and response.status_code in RETRY_STATUSES


def _wait(state: RetryCallState) -> float:
    outcome = state.outcome
    if outcome is not None and not outcome.failed:
        delay = retry_after_seconds(outcome.result())
        if delay is not None:
            return delay
    return _backoff(state)


def _reason(state: RetryCallState) -> str:
    outcome = state.outcome
    if outcome is None:
        return "unknown"
    if outcome.failed:
        return type(outcome.exception()).__name__
    return f"HTTP {outcome.result().status_code}"


async def send_with_retry(
    client: httpx.AsyncClient,
    method: str,
    url: str,
    *,
    params: Mapping[str, Any] | None = None,
    headers: Mapping[str, str] | None = None,
    json: Any = None,
    data: Mapping[str, Any] | None = None,
    timeout_s: float | None = None,
) -> httpx.Response:
    """Send a request, retrying transient failures.

    Returns the final response (which may be a 4xx for the caller to interpret); raises
    UpstreamUnavailable when the host stays unreachable or keeps answering 429/5xx.
    `timeout_s` overrides the client default for slow endpoints.
    """
    request = client.build_request(
        method,
        url,
        params=params,
        headers=headers,
        json=json,
        data=data,
        timeout=timeout_s if timeout_s is not None else client.timeout,
    )
    host = request.url.host
    limiter: AbstractAsyncContextManager[None] = host_limiter(host) or nullcontext()

    def before_sleep(state: RetryCallState) -> None:
        wait_s = state.next_action.sleep if state.next_action else None
        log.warning(
            "upstream_retry",
            host=host,
            attempt=state.attempt_number,
            reason=_reason(state),
            wait_s=wait_s,
        )

    def give_up(state: RetryCallState) -> None:
        log.error(
            "upstream_gave_up", host=host, attempts=state.attempt_number, reason=_reason(state)
        )

    retrying = AsyncRetrying(
        stop=stop_after_attempt(MAX_ATTEMPTS),
        wait=_wait,
        retry=retry_if_exception_type(RETRY_EXCEPTIONS) | retry_if_result(_is_retryable),
        sleep=_sleep,
        before_sleep=before_sleep,
        retry_error_callback=give_up,
    )
    response: httpx.Response | None = None
    try:
        async for attempt in retrying:
            with attempt:
                response = None
                async with limiter:
                    response = await client.send(request)
            outcome = attempt.retry_state.outcome
            if outcome is not None and not outcome.failed:
                attempt.retry_state.set_result(response)
    except httpx.TransportError as exc:
        log.error("upstream_error", host=host, reason=type(exc).__name__)
        raise UpstreamUnavailable(f"{host} is unreachable") from exc
    if response is None:
        raise UpstreamUnavailable(f"{host} is unreachable")
    if response.status_code in RETRY_STATUSES or response.is_server_error:
        raise UpstreamUnavailable(f"{host} answered HTTP {response.status_code}")
    return response


def parse_json(response: httpx.Response) -> Any:
    """JSON body of a successful response; anything else means the upstream is unusable."""
    host = response.request.url.host
    if response.is_error:
        log.warning(
            "upstream_http_error", host=host, status=response.status_code, body=response.text[:300]
        )
        raise UpstreamUnavailable(f"{host} answered HTTP {response.status_code}")
    try:
        return response.json()
    except ValueError as exc:
        raise UpstreamUnavailable(f"{host} sent an unreadable response") from exc


async def fetch_json(
    client: httpx.AsyncClient,
    method: str,
    url: str,
    *,
    params: Mapping[str, Any] | None = None,
    headers: Mapping[str, str] | None = None,
    json: Any = None,
    data: Mapping[str, Any] | None = None,
    timeout_s: float | None = None,
) -> Any:
    response = await send_with_retry(
        client,
        method,
        url,
        params=params,
        headers=headers,
        json=json,
        data=data,
        timeout_s=timeout_s,
    )
    return parse_json(response)
