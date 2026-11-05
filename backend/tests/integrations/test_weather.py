from datetime import date, timedelta
from typing import Any

import httpx
import respx

from app.integrations.ports import GeoPoint
from app.integrations.weather.open_meteo import WMO_SUMMARIES, OpenMeteoWeather, describe

FORECAST = "https://api.open-meteo.com/v1/forecast"
ARCHIVE = "https://archive-api.open-meteo.com/v1/archive"
TODAY = date(2026, 11, 5)
POKHARA = GeoPoint(lat=28.20961, lon=83.98559)


def _daily(days: list[date], *, probability: bool) -> dict[str, Any]:
    daily: dict[str, list[Any]] = {
        "time": [d.isoformat() for d in days],
        "weather_code": [0, 61, 3, 95][: len(days)] + [2] * max(0, len(days) - 4),
        "temperature_2m_max": [24.1] * len(days),
        "temperature_2m_min": [11.3] * len(days),
        "precipitation_sum": [0.0, 4.2, None, 12.5][: len(days)] + [0.0] * max(0, len(days) - 4),
    }
    units = {"time": "iso8601", "temperature_2m_max": "°C", "precipitation_sum": "mm"}
    if probability:
        daily["precipitation_probability_max"] = [5, 70, None, 90][: len(days)] + [10] * max(
            0, len(days) - 4
        )
    return {
        "latitude": 28.2,
        "longitude": 84.0,
        "generationtime_ms": 0.08,
        "utc_offset_seconds": 20700,
        "timezone": "Asia/Kathmandu",
        "timezone_abbreviation": "GMT+5:45",
        "elevation": 827.0,
        "daily_units": units,
        "daily": daily,
    }


def _span(start: date, end: date) -> list[date]:
    return [start + timedelta(days=i) for i in range((end - start).days + 1)]


def _weather(http: httpx.AsyncClient) -> OpenMeteoWeather:
    return OpenMeteoWeather(http, today=lambda: TODAY)


async def test_forecast_inside_window(
    http: httpx.AsyncClient, respx_mock: respx.MockRouter
) -> None:
    start, end = TODAY + timedelta(days=2), TODAY + timedelta(days=5)
    route = respx_mock.get(FORECAST).respond(json=_daily(_span(start, end), probability=True))

    days = await _weather(http).daily(POKHARA, start, end)

    params = route.calls.last.request.url.params
    assert params["daily"] == (
        "weather_code,temperature_2m_max,temperature_2m_min,precipitation_sum,precipitation_probability_max"
    )
    assert params["timezone"] == "auto"
    assert (params["start_date"], params["end_date"]) == ("2026-11-07", "2026-11-10")
    assert (params["latitude"], params["longitude"]) == ("28.21", "83.99")
    assert [d.day for d in days] == _span(start, end)
    assert [d.summary for d in days] == ["Clear sky", "Light rain", "Overcast", "Thunderstorm"]
    assert days[1].precipitation_probability == 70
    assert days[2].precipitation_mm == 0.0
    assert not any(d.is_climate_estimate for d in days)


async def test_beyond_window_uses_last_years_weather(
    http: httpx.AsyncClient, respx_mock: respx.MockRouter
) -> None:
    start, end = date(2027, 3, 1), date(2027, 3, 3)
    route = respx_mock.get(ARCHIVE).respond(
        json=_daily(_span(date(2026, 3, 1), date(2026, 3, 3)), probability=False)
    )

    days = await _weather(http).daily(POKHARA, start, end)

    params = route.calls.last.request.url.params
    assert (params["start_date"], params["end_date"]) == ("2026-03-01", "2026-03-03")
    assert "precipitation_probability_max" not in params["daily"]
    assert [d.day for d in days] == _span(start, end)
    assert all(d.is_climate_estimate for d in days)
    assert all(d.precipitation_probability is None for d in days)


async def test_far_future_goes_back_until_the_archive_has_data(
    http: httpx.AsyncClient, respx_mock: respx.MockRouter
) -> None:
    start = end = date(2027, 11, 3)
    route = respx_mock.get(ARCHIVE).respond(json=_daily([date(2025, 11, 3)], probability=False))

    days = await _weather(http).daily(POKHARA, start, end)

    assert route.calls.last.request.url.params["start_date"] == "2025-11-03"
    assert [d.day for d in days] == [start]


async def test_range_straddling_the_horizon_is_split(
    http: httpx.AsyncClient, respx_mock: respx.MockRouter
) -> None:
    start, end = TODAY + timedelta(days=12), TODAY + timedelta(days=17)
    horizon = TODAY + timedelta(days=14)
    forecast = respx_mock.get(FORECAST).respond(
        json=_daily(_span(start, horizon), probability=True)
    )
    archive = respx_mock.get(ARCHIVE).respond(
        json=_daily(
            _span(horizon + timedelta(days=1) - timedelta(days=365), end - timedelta(days=365)),
            probability=False,
        )
    )

    days = await _weather(http).daily(POKHARA, start, end)

    assert forecast.calls.last.request.url.params["end_date"] == horizon.isoformat()
    assert archive.calls.last.request.url.params["start_date"] == "2025-11-20"
    assert [d.day for d in days] == _span(start, end)
    assert [d.is_climate_estimate for d in days] == [False] * 3 + [True] * 3


async def test_forecast_is_cached(http: httpx.AsyncClient, respx_mock: respx.MockRouter) -> None:
    route = respx_mock.get(FORECAST).respond(json=_daily([TODAY], probability=True))
    weather = _weather(http)
    await weather.daily(POKHARA, TODAY, TODAY)
    await weather.daily(GeoPoint(lat=28.2104, lon=83.9861), TODAY, TODAY)
    assert route.call_count == 1


async def test_end_before_start_is_empty(http: httpx.AsyncClient) -> None:
    assert await _weather(http).daily(POKHARA, TODAY, TODAY - timedelta(days=1)) == []


def test_wmo_summaries() -> None:
    assert describe(0) == "Clear sky"
    assert describe(65) == "Heavy rain"
    assert describe(1234) == "Unknown"
    assert len(WMO_SUMMARIES) == 28
