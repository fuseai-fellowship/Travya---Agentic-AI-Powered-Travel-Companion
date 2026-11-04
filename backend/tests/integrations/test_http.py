from datetime import UTC, datetime, timedelta
from email.utils import format_datetime
from types import TracebackType

import httpx
import pytest
import respx

from app.core.config import Settings
from app.core.errors import UpstreamUnavailable
from app.integrations import http as http_module
from app.integrations.http import (
    MAX_ATTEMPTS,
    create_http_client,
    fetch_json,
    host_limiter,
    retry_after_seconds,
    send_with_retry,
)

URL = "https://api.example.org/data"


async def test_client_identifies_itself(settings: Settings, respx_mock: respx.MockRouter) -> None:
    route = respx_mock.get(URL).respond(json={"ok": True})
    async with create_http_client(settings) as client:
        assert client.timeout.read == settings.HTTP_TIMEOUT_SECONDS
        assert client.follow_redirects is True
        await client.get(URL)
    assert route.calls.last.request.headers["User-Agent"] == settings.HTTP_USER_AGENT


async def test_retries_503_then_succeeds(
    http: httpx.AsyncClient, respx_mock: respx.MockRouter, sleeps: list[float]
) -> None:
    route = respx_mock.get(URL).mock(
        side_effect=[httpx.Response(503), httpx.Response(200, json={"ok": True})]
    )
    assert await fetch_json(http, "GET", URL) == {"ok": True}
    assert route.call_count == 2
    assert len(sleeps) == 1
    assert 0 < sleeps[0] <= 1.0


async def test_retries_connect_errors(
    http: httpx.AsyncClient, respx_mock: respx.MockRouter, sleeps: list[float]
) -> None:
    route = respx_mock.get(URL).mock(
        side_effect=[httpx.ConnectError("refused"), httpx.Response(200, json=[1])]
    )
    assert await fetch_json(http, "GET", URL) == [1]
    assert route.call_count == 2


async def test_gives_up_after_max_attempts(
    http: httpx.AsyncClient, respx_mock: respx.MockRouter, sleeps: list[float]
) -> None:
    route = respx_mock.get(URL).respond(502)
    with pytest.raises(UpstreamUnavailable, match="502"):
        await send_with_retry(http, "GET", URL)
    assert route.call_count == MAX_ATTEMPTS
    assert len(sleeps) == MAX_ATTEMPTS - 1


async def test_persistent_read_timeout_is_upstream_unavailable(
    http: httpx.AsyncClient, respx_mock: respx.MockRouter, sleeps: list[float]
) -> None:
    route = respx_mock.get(URL).mock(side_effect=httpx.ReadTimeout("slow"))
    with pytest.raises(UpstreamUnavailable, match="unreachable"):
        await send_with_retry(http, "GET", URL)
    assert route.call_count == MAX_ATTEMPTS


async def test_honours_retry_after_up_to_ten_seconds(
    http: httpx.AsyncClient, respx_mock: respx.MockRouter, sleeps: list[float]
) -> None:
    respx_mock.get(URL).mock(
        side_effect=[
            httpx.Response(429, headers={"Retry-After": "3"}),
            httpx.Response(429, headers={"Retry-After": "120"}),
            httpx.Response(200, json={}),
        ]
    )
    await send_with_retry(http, "GET", URL)
    assert sleeps == [3.0, 10.0]


def test_retry_after_accepts_http_dates() -> None:
    when = datetime.now(UTC) + timedelta(seconds=5)
    response = httpx.Response(503, headers={"Retry-After": format_datetime(when, usegmt=True)})
    delay = retry_after_seconds(response)
    assert delay is not None
    assert 3 <= delay <= 5
    assert retry_after_seconds(httpx.Response(503, headers={"Retry-After": "soon"})) is None


async def test_client_errors_are_not_retried(
    http: httpx.AsyncClient, respx_mock: respx.MockRouter, sleeps: list[float]
) -> None:
    route = respx_mock.get(URL).respond(404)
    response = await send_with_retry(http, "GET", URL)
    assert response.status_code == 404
    assert route.call_count == 1
    with pytest.raises(UpstreamUnavailable, match="404"):
        await fetch_json(http, "GET", URL)


async def test_invalid_json_is_upstream_unavailable(
    http: httpx.AsyncClient, respx_mock: respx.MockRouter
) -> None:
    respx_mock.get(URL).respond(200, text="<html>maintenance</html>")
    with pytest.raises(UpstreamUnavailable, match="unreadable"):
        await fetch_json(http, "GET", URL)


def test_nominatim_has_a_one_per_second_limiter() -> None:
    limiter = host_limiter("nominatim.openstreetmap.org")
    assert limiter is not None
    assert (limiter.max_rate, limiter.time_period) == (1, 1)
    assert host_limiter("nominatim.openstreetmap.org") is limiter
    assert host_limiter("api.open-meteo.com") is None


class _CountingLimiter:
    def __init__(self) -> None:
        self.entered = 0

    async def __aenter__(self) -> None:
        self.entered += 1

    async def __aexit__(
        self,
        exc_type: type[BaseException] | None,
        exc: BaseException | None,
        tb: TracebackType | None,
    ) -> None:
        return None


async def test_every_attempt_waits_for_the_host_limiter(
    http: httpx.AsyncClient,
    respx_mock: respx.MockRouter,
    sleeps: list[float],
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    limiter = _CountingLimiter()
    monkeypatch.setitem(http_module._limiters, "nominatim.openstreetmap.org", limiter)
    respx_mock.get("https://nominatim.openstreetmap.org/status").mock(
        side_effect=[httpx.Response(503), httpx.Response(200, json={})]
    )
    await send_with_retry(http, "GET", "https://nominatim.openstreetmap.org/status")
    assert limiter.entered == 2
