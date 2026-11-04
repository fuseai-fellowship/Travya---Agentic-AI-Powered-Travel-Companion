"""Daily weather from Open-Meteo: forecast inside its 16-day window, last year's weather beyond it."""

from collections.abc import Callable
from datetime import UTC, date, datetime, timedelta
from typing import Any

import httpx
from cashews import cache

from app.integrations.caching import CLIMATE_TTL, FORECAST_TTL, non_empty
from app.integrations.http import fetch_json
from app.integrations.ports import DailyWeather, GeoPoint

FORECAST_URL = "https://api.open-meteo.com/v1/forecast"
ARCHIVE_URL = "https://archive-api.open-meteo.com/v1/archive"
FORECAST_DAYS = 16
# Archive data trails real time by a few days.
ARCHIVE_LAG_DAYS = 7
_FORECAST_DAILY = "weather_code,temperature_2m_max,temperature_2m_min,precipitation_sum,precipitation_probability_max"
_ARCHIVE_DAILY = "weather_code,temperature_2m_max,temperature_2m_min,precipitation_sum"

WMO_SUMMARIES: dict[int, str] = {
    0: "Clear sky",
    1: "Mainly clear",
    2: "Partly cloudy",
    3: "Overcast",
    45: "Fog",
    48: "Freezing fog",
    51: "Light drizzle",
    53: "Drizzle",
    55: "Heavy drizzle",
    56: "Light freezing drizzle",
    57: "Freezing drizzle",
    61: "Light rain",
    63: "Rain",
    65: "Heavy rain",
    66: "Light freezing rain",
    67: "Freezing rain",
    71: "Light snow",
    73: "Snow",
    75: "Heavy snow",
    77: "Snow grains",
    80: "Light showers",
    81: "Showers",
    82: "Violent showers",
    85: "Light snow showers",
    86: "Heavy snow showers",
    95: "Thunderstorm",
    96: "Thunderstorm with hail",
    99: "Thunderstorm with heavy hail",
}


def describe(weather_code: int) -> str:
    return WMO_SUMMARIES.get(weather_code, "Unknown")


def _utc_today() -> date:
    return datetime.now(UTC).date()


class OpenMeteoWeather:
    def __init__(
        self,
        http: httpx.AsyncClient,
        *,
        forecast_url: str = FORECAST_URL,
        archive_url: str = ARCHIVE_URL,
        today: Callable[[], date] = _utc_today,
    ) -> None:
        self._http = http
        self._forecast_url = forecast_url
        self._archive_url = archive_url
        self._today = today

    async def daily(self, point: GeoPoint, start: date, end: date) -> list[DailyWeather]:
        if end < start:
            return []
        lat, lon = round(point.lat, 2), round(point.lon, 2)
        # one day of slack: the window is counted in the destination's time zone
        horizon = self._today() + timedelta(days=FORECAST_DAYS - 2)
        days: list[DailyWeather] = []
        if start <= horizon:
            days += await self._forecast(lat, lon, start, min(end, horizon))
        if end > horizon:
            days += await self._climate(lat, lon, max(start, horizon + timedelta(days=1)), end)
        return days

    @cache(
        ttl=FORECAST_TTL, key="open-meteo:forecast:{lat}:{lon}:{start}:{end}", condition=non_empty
    )
    async def _forecast(self, lat: float, lon: float, start: date, end: date) -> list[DailyWeather]:
        data = await fetch_json(
            self._http,
            "GET",
            self._forecast_url,
            params=_params(lat, lon, start, end, _FORECAST_DAILY),
        )
        return parse_daily(data)

    @cache(ttl=CLIMATE_TTL, key="open-meteo:climate:{lat}:{lon}:{start}:{end}", condition=non_empty)
    async def _climate(self, lat: float, lon: float, start: date, end: date) -> list[DailyWeather]:
        latest = self._today() - timedelta(days=ARCHIVE_LAG_DAYS)
        years = 1
        while _years_back(end, years) > latest:
            years += 1
        targets = [start + timedelta(days=i) for i in range((end - start).days + 1)]
        sources = {day: _years_back(day, years) for day in targets}
        data = await fetch_json(
            self._http,
            "GET",
            self._archive_url,
            params=_params(lat, lon, sources[start], sources[end], _ARCHIVE_DAILY),
        )
        observed = {day.day: day for day in parse_daily(data)}
        return [
            observed[source].model_copy(update={"day": day, "is_climate_estimate": True})
            for day, source in sources.items()
            if source in observed
        ]


def _params(lat: float, lon: float, start: date, end: date, daily: str) -> dict[str, Any]:
    return {
        "latitude": lat,
        "longitude": lon,
        "daily": daily,
        "timezone": "auto",
        "start_date": start.isoformat(),
        "end_date": end.isoformat(),
    }


def _years_back(day: date, years: int) -> date:
    try:
        return day.replace(year=day.year - years)
    except ValueError:  # 29 February
        return day.replace(year=day.year - years, day=28)


def parse_daily(data: dict[str, Any]) -> list[DailyWeather]:
    daily: dict[str, list[Any]] = data.get("daily") or {}
    times = daily.get("time") or []

    def column(name: str) -> list[Any]:
        return daily.get(name) or [None] * len(times)

    rows = zip(
        times,
        column("weather_code"),
        column("temperature_2m_min"),
        column("temperature_2m_max"),
        column("precipitation_sum"),
        column("precipitation_probability_max"),
        strict=True,
    )
    days: list[DailyWeather] = []
    for day, code, t_min, t_max, precipitation, probability in rows:
        if code is None or t_min is None or t_max is None:
            continue
        days.append(
            DailyWeather(
                day=date.fromisoformat(day),
                temp_min_c=t_min,
                temp_max_c=t_max,
                precipitation_mm=precipitation or 0.0,
                precipitation_probability=probability,
                weather_code=int(code),
                summary=describe(int(code)),
            )
        )
    return days
