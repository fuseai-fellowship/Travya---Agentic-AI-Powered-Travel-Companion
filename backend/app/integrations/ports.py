"""Ports: what the app needs from the outside world.

Each port has a real adapter (OpenStreetMap services, Open-Meteo, Wikivoyage, Unsplash, ...) and a
fake used by tests and offline demos. Services and agents depend only on these protocols.
"""

from datetime import date
from decimal import Decimal
from typing import Any, Literal, Protocol

from pydantic import BaseModel, Field

PoiCategory = Literal[
    "attraction",
    "museum",
    "viewpoint",
    "park",
    "restaurant",
    "cafe",
    "nightlife",
    "shopping",
    "religious",
    "hotel",
]
RouteProfile = Literal["foot", "car", "bike"]


class GeoPoint(BaseModel):
    lat: float = Field(ge=-90, le=90)
    lon: float = Field(ge=-180, le=180)


class Place(BaseModel):
    name: str
    display_name: str
    lat: float
    lon: float
    category: str | None = None
    country_code: str | None = None
    address: str | None = None
    opening_hours: str | None = None
    website: str | None = None
    osm_ref: str | None = Field(
        default=None, description="e.g. 'node/123' for attribution and dedupe"
    )
    source: str


class Route(BaseModel):
    profile: RouteProfile
    distance_m: float
    duration_s: float
    geometry: list[tuple[float, float]] = Field(description="[lon, lat] pairs (GeoJSON order)")
    source: str


class DailyWeather(BaseModel):
    day: date
    temp_min_c: float
    temp_max_c: float
    precipitation_mm: float
    precipitation_probability: int | None = None
    weather_code: int
    summary: str
    is_climate_estimate: bool = Field(
        default=False,
        description="True when the date is beyond the forecast range and climate normals are used",
    )


class GuideSection(BaseModel):
    title: str
    text: str


class DestinationGuide(BaseModel):
    destination: str
    summary: str
    sections: list[GuideSection]
    url: str
    source: str
    license: str = "CC BY-SA 4.0"


class Photo(BaseModel):
    url: str
    thumb_url: str
    width: int
    height: int
    alt: str
    author_name: str
    author_url: str | None = None
    source: str
    source_url: str
    download_location: str | None = Field(
        default=None, description="Unsplash download-tracking endpoint"
    )


class TravelOffer(BaseModel):
    kind: Literal["flight", "hotel"]
    title: str
    provider: str
    amount: Decimal
    currency: str
    details: dict[str, Any]
    is_sample: bool = Field(
        description="Sample fares are illustrative; bookings in Travya are simulated"
    )


class Geocoder(Protocol):
    async def search(self, query: str, *, limit: int = 5) -> list[Place]: ...

    async def reverse(self, point: GeoPoint) -> Place | None: ...


class Autocomplete(Protocol):
    async def suggest(
        self, query: str, *, limit: int = 6, near: GeoPoint | None = None
    ) -> list[Place]: ...


class PlacesSearch(Protocol):
    async def nearby(
        self,
        center: GeoPoint,
        *,
        categories: list[PoiCategory],
        radius_m: int = 3000,
        limit: int = 30,
    ) -> list[Place]: ...


class Router(Protocol):
    async def route(
        self, points: list[GeoPoint], *, profile: RouteProfile = "foot"
    ) -> Route | None: ...


class WeatherProvider(Protocol):
    async def daily(self, point: GeoPoint, start: date, end: date) -> list[DailyWeather]: ...


class GuideProvider(Protocol):
    async def guide(self, destination: str) -> DestinationGuide | None: ...


class PhotoProvider(Protocol):
    async def search(self, query: str, *, limit: int = 6) -> list[Photo]: ...

    async def track_download(self, photo: Photo) -> None: ...


class OffersProvider(Protocol):
    async def flights(
        self,
        *,
        origin: str | None,
        destination: str,
        depart: date,
        return_date: date | None,
        travelers: int,
        currency: str,
    ) -> list[TravelOffer]: ...

    async def hotels(
        self,
        *,
        destination: str,
        check_in: date,
        check_out: date,
        travelers: int,
        nightly_budget: Decimal | None,
        currency: str,
    ) -> list[TravelOffer]: ...


class ObjectStorage(Protocol):
    async def put(self, key: str, data: bytes, content_type: str) -> None: ...

    async def get(self, key: str) -> bytes: ...

    async def delete(self, key: str) -> None: ...

    async def download_url(self, key: str, filename: str, expires_s: int = 600) -> str | None:
        """Signed URL, or None when the API must stream the file itself (local storage)."""
        ...
