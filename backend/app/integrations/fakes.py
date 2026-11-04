"""Deterministic, network-free implementation of every port, for tests and offline demos.

A few real cities resolve to their true coordinates; anything else gets stable hash-based ones.
"""

import hashlib
import re
from datetime import UTC, date, datetime, timedelta
from itertools import pairwise
from math import cos, pi, radians, sin, sqrt
from typing import NamedTuple
from urllib.parse import quote

from app.core.errors import NotFound
from app.integrations.geo import haversine_m
from app.integrations.guides.wikivoyage import page_title
from app.integrations.ports import (
    DailyWeather,
    DestinationGuide,
    GeoPoint,
    GuideSection,
    Photo,
    Place,
    PoiCategory,
    Route,
    RouteProfile,
)
from app.integrations.storage import validate_key
from app.integrations.weather.open_meteo import FORECAST_DAYS, describe

SOURCE = "fake"


class City(NamedTuple):
    name: str
    lat: float
    lon: float
    country_code: str
    region: str


KNOWN_CITIES: dict[str, City] = {
    "kathmandu": City("Kathmandu", 27.7172, 85.3240, "NP", "Bagmati Province, Nepal"),
    "pokhara": City("Pokhara", 28.2096, 83.9856, "NP", "Gandaki Province, Nepal"),
    "paris": City("Paris", 48.8566, 2.3522, "FR", "Ile-de-France, France"),
    "tokyo": City("Tokyo", 35.6762, 139.6503, "JP", "Japan"),
    "lisbon": City("Lisbon", 38.7223, -9.1393, "PT", "Lisbon, Portugal"),
    "new york": City("New York", 40.7128, -74.0060, "US", "New York, United States"),
}

_POI_NOUNS: dict[PoiCategory, str] = {
    "attraction": "Square",
    "museum": "Museum",
    "viewpoint": "Viewpoint",
    "park": "Park",
    "restaurant": "Kitchen",
    "cafe": "Cafe",
    "nightlife": "Bar",
    "shopping": "Market",
    "religious": "Temple",
    "hotel": "Hotel",
}
_POI_WORDS = ("Riverside", "Old Town", "Lotus", "Harbour", "Hilltop", "Garden", "Lantern", "Cedar")
_SPEEDS_M_S: dict[RouteProfile, float] = {"foot": 1.3, "bike": 4.2, "car": 11.0}
_GOLDEN_ANGLE = pi * (3 - sqrt(5))
# (upper bound of a 0..1 roll, WMO code, precipitation mm)
_WEATHER_ROLLS = (
    (0.3, 0, 0.0),
    (0.5, 1, 0.0),
    (0.7, 2, 0.0),
    (0.82, 3, 0.2),
    (0.92, 61, 2.5),
    (0.98, 63, 8.0),
    (1.0, 95, 15.0),
)
_METRES_PER_DEGREE = 111_320.0


def _unit(*parts: object) -> float:
    """Stable pseudo-random number in [0, 1) derived from the parts."""
    digest = hashlib.blake2b("|".join(map(str, parts)).encode(), digest_size=8).digest()
    return int.from_bytes(digest) / 2**64


def _city_place(city: City) -> Place:
    return Place(
        name=city.name,
        display_name=f"{city.name}, {city.region}",
        lat=city.lat,
        lon=city.lon,
        category="city",
        country_code=city.country_code,
        source=SOURCE,
    )


def _hashed_place(query: str) -> Place:
    name = " ".join(query.split()).title()
    return Place(
        name=name,
        display_name=name,
        lat=round(-55 + 125 * _unit(name.casefold(), "lat"), 4),
        lon=round(-180 + 360 * _unit(name.casefold(), "lon"), 4),
        category="city",
        source=SOURCE,
    )


def _offset(center: GeoPoint, distance_m: float, angle: float) -> tuple[float, float]:
    lat = center.lat + distance_m * cos(angle) / _METRES_PER_DEGREE
    lon = center.lon + distance_m * sin(angle) / (
        _METRES_PER_DEGREE * max(cos(radians(center.lat)), 0.01)
    )
    return round(max(-90.0, min(90.0, lat)), 6), round((lon + 180) % 360 - 180, 6)


class FakeGeocoder:
    async def search(self, query: str, *, limit: int = 5) -> list[Place]:
        needle = " ".join(query.split()).casefold()
        if not needle:
            return []
        matches = [city for key, city in KNOWN_CITIES.items() if needle in key or key in needle]
        places = [_city_place(city) for city in matches] or [_hashed_place(query)]
        return places[:limit]

    async def reverse(self, point: GeoPoint) -> Place | None:
        nearest = min(
            KNOWN_CITIES.values(), key=lambda c: haversine_m(point.lat, point.lon, c.lat, c.lon)
        )
        if haversine_m(point.lat, point.lon, nearest.lat, nearest.lon) < 50_000:
            return _city_place(nearest)
        label = f"{point.lat:.4f}, {point.lon:.4f}"
        return Place(name=label, display_name=label, lat=point.lat, lon=point.lon, source=SOURCE)


class FakeAutocomplete:
    async def suggest(
        self, query: str, *, limit: int = 6, near: GeoPoint | None = None
    ) -> list[Place]:
        needle = " ".join(query.split()).casefold()
        if len(needle) < 2:
            return []
        matches = [city for key, city in KNOWN_CITIES.items() if key.startswith(needle)]
        if near is not None:
            matches.sort(key=lambda c: haversine_m(near.lat, near.lon, c.lat, c.lon))
        places = [_city_place(city) for city in matches] or [_hashed_place(query)]
        return places[:limit]


class FakePlaces:
    async def nearby(
        self,
        center: GeoPoint,
        *,
        categories: list[PoiCategory],
        radius_m: int = 3000,
        limit: int = 30,
    ) -> list[Place]:
        if not categories or limit <= 0:
            return []
        places: list[Place] = []
        for i in range(limit):
            category = categories[i % len(categories)]
            word = _POI_WORDS[int(_unit(center.lat, center.lon, i) * len(_POI_WORDS))]
            name = f"{word} {_POI_NOUNS[category]} {i // len(_POI_WORDS) + 1}"
            # spread points evenly over the disc (sunflower pattern)
            lat, lon = _offset(center, 0.9 * radius_m * sqrt((i + 0.5) / limit), i * _GOLDEN_ANGLE)
            places.append(
                Place(
                    name=name,
                    display_name=name,
                    lat=lat,
                    lon=lon,
                    category=category,
                    opening_hours="Mo-Su 09:00-18:00",
                    source=SOURCE,
                )
            )
        return places


class FakeRouter:
    async def route(
        self, points: list[GeoPoint], *, profile: RouteProfile = "foot"
    ) -> Route | None:
        if len(points) < 2:
            return None
        straight = sum(haversine_m(a.lat, a.lon, b.lat, b.lon) for a, b in pairwise(points))
        distance = straight * 1.25  # streets are rarely straight
        return Route(
            profile=profile,
            distance_m=round(distance, 1),
            duration_s=round(distance / _SPEEDS_M_S[profile], 1),
            geometry=[(p.lon, p.lat) for p in points],
            source=SOURCE,
        )


class FakeWeather:
    def __init__(self, today: date | None = None) -> None:
        self._today = today

    async def daily(self, point: GeoPoint, start: date, end: date) -> list[DailyWeather]:
        today = self._today or datetime.now(UTC).date()
        horizon = today + timedelta(days=FORECAST_DAYS - 2)
        hemisphere = 1 if point.lat >= 0 else -1
        amplitude = 12 * min(abs(point.lat) / 60, 1)
        days: list[DailyWeather] = []
        for offset in range((end - start).days + 1):
            day = start + timedelta(days=offset)
            season = cos(2 * pi * (day.timetuple().tm_yday - 196) / 365) * hemisphere
            mean = 28 - 0.35 * abs(point.lat) + amplitude * season
            roll = _unit(round(point.lat, 2), round(point.lon, 2), day)
            code, rain = next((c, r) for limit, c, r in _WEATHER_ROLLS if roll < limit)
            days.append(
                DailyWeather(
                    day=day,
                    temp_min_c=round(mean - 4 - 2 * roll, 1),
                    temp_max_c=round(mean + 4 + 2 * roll, 1),
                    precipitation_mm=rain,
                    precipitation_probability=None if day > horizon else round(roll * 100),
                    weather_code=code,
                    summary=describe(code),
                    is_climate_estimate=day > horizon,
                )
            )
        return days


class FakeGuides:
    async def guide(self, destination: str) -> DestinationGuide | None:
        title = page_title(destination)
        if not title:
            return None
        sections = {
            "Understand": f"{title} rewards slow travel: give it at least two full days.",
            "Get around": f"The centre of {title} is compact and best explored on foot; taxis fill the gaps.",
            "See": f"Start in the old quarter of {title}, then head to a viewpoint for sunset.",
            "Eat": "Try the local market for breakfast and a family-run place for dinner.",
            "Stay safe": "Keep valuables close in crowded areas and carry a copy of your passport.",
        }
        return DestinationGuide(
            destination=title,
            summary=f"{title} is shown with sample guide text while Travya runs offline.",
            sections=[GuideSection(title=name, text=text) for name, text in sections.items()],
            url=f"https://en.wikivoyage.org/wiki/{title.replace(' ', '_')}",
            source=SOURCE,
        )


class FakePhotos:
    def __init__(self) -> None:
        self.tracked: list[Photo] = []

    async def search(self, query: str, *, limit: int = 6) -> list[Photo]:
        slug = re.sub(r"[^a-z0-9]+", "-", query.casefold()).strip("-") or "travel"
        return [
            Photo(
                url=_placeholder(f"{slug}-{i}", query),
                thumb_url=_placeholder(f"{slug}-{i}", query),
                width=800,
                height=533,
                alt=f"{query} (sample photo {i + 1})",
                author_name="Travya sample image",
                author_url=None,
                source="sample",
                source_url="https://github.com/fuseai-fellowship/Travya---Agentic-AI-Powered-Travel-Companion",
            )
            for i in range(limit)
        ]

    async def track_download(self, photo: Photo) -> None:
        self.tracked.append(photo)


def _placeholder(seed: str, label: str) -> str:
    """An inline SVG gradient, so offline demos need no image host (and pass the CSP)."""
    digest = hashlib.sha256(seed.encode()).hexdigest()
    a, b = f"#{digest[:6]}", f"#{digest[6:12]}"
    text = re.sub(r"[^A-Za-z0-9 ,.-]", "", label)[:32]
    svg = (
        "<svg xmlns='http://www.w3.org/2000/svg' width='800' height='533'>"
        f"<defs><linearGradient id='g' x2='1' y2='1'><stop offset='0' stop-color='{a}'/>"
        f"<stop offset='1' stop-color='{b}'/></linearGradient></defs>"
        "<rect width='800' height='533' fill='url(#g)'/>"
        "<text x='40' y='490' font-family='sans-serif' font-size='36' fill='white'>"
        f"{text}</text></svg>"
    )
    return "data:image/svg+xml," + quote(svg, safe=" ='/:,.-#")


class MemoryStorage:
    def __init__(self) -> None:
        self.objects: dict[str, tuple[bytes, str]] = {}

    async def put(self, key: str, data: bytes, content_type: str) -> None:
        self.objects[validate_key(key)] = (data, content_type)

    async def get(self, key: str) -> bytes:
        try:
            return self.objects[validate_key(key)][0]
        except KeyError as exc:
            raise NotFound("File not found") from exc

    async def delete(self, key: str) -> None:
        self.objects.pop(validate_key(key), None)

    async def download_url(self, key: str, filename: str, expires_s: int = 600) -> str | None:
        validate_key(key)
        return None
