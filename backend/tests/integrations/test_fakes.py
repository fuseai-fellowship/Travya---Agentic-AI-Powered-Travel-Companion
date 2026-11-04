import inspect
from datetime import date, timedelta
from typing import Any

import pytest

from app.core.errors import NotFound
from app.integrations import ports
from app.integrations.fakes import (
    KNOWN_CITIES,
    FakeAutocomplete,
    FakeGeocoder,
    FakeGuides,
    FakePhotos,
    FakePlaces,
    FakeRouter,
    FakeWeather,
    MemoryStorage,
)
from app.integrations.geo import haversine_m
from app.integrations.geocoding.nominatim import NominatimGeocoder
from app.integrations.geocoding.photon import PhotonAutocomplete
from app.integrations.guides.wikivoyage import WikivoyageGuides
from app.integrations.offers.sample import SampleOffers
from app.integrations.photos import FallbackPhotos
from app.integrations.photos.unsplash import UnsplashPhotos
from app.integrations.photos.wikimedia import WikimediaPhotos
from app.integrations.places.overpass import OverpassPlaces
from app.integrations.routing import FallbackRouter
from app.integrations.routing.ors import OrsRouter
from app.integrations.routing.osrm import OsrmRouter
from app.integrations.storage.gcs import GcsStorage
from app.integrations.storage.local import LocalStorage
from app.integrations.weather.open_meteo import OpenMeteoWeather

IMPLEMENTATIONS: list[tuple[type[Any], list[type[Any]]]] = [
    (ports.Geocoder, [FakeGeocoder, NominatimGeocoder]),
    (ports.Autocomplete, [FakeAutocomplete, PhotonAutocomplete]),
    (ports.PlacesSearch, [FakePlaces, OverpassPlaces]),
    (ports.Router, [FakeRouter, OsrmRouter, OrsRouter, FallbackRouter]),
    (ports.WeatherProvider, [FakeWeather, OpenMeteoWeather]),
    (ports.GuideProvider, [FakeGuides, WikivoyageGuides]),
    (ports.PhotoProvider, [FakePhotos, UnsplashPhotos, WikimediaPhotos, FallbackPhotos]),
    (ports.OffersProvider, [SampleOffers]),
    (ports.ObjectStorage, [MemoryStorage, LocalStorage, GcsStorage]),
]
KATHMANDU = ports.GeoPoint(lat=27.7172, lon=85.3240)


def _protocol_methods(protocol: type[Any]) -> list[str]:
    return [name for name, value in vars(protocol).items() if inspect.iscoroutinefunction(value)]


@pytest.mark.parametrize(
    ("protocol", "implementation"),
    [(protocol, impl) for protocol, impls in IMPLEMENTATIONS for impl in impls],
    ids=lambda value: getattr(value, "__name__", ""),
)
def test_implementation_matches_protocol(protocol: type[Any], implementation: type[Any]) -> None:
    for name in _protocol_methods(protocol):
        method = getattr(implementation, name)
        assert inspect.iscoroutinefunction(method), f"{implementation.__name__}.{name} is not async"
        expected = inspect.signature(getattr(protocol, name))
        actual = inspect.signature(method)
        assert [(p.name, p.kind, p.default) for p in actual.parameters.values()] == [
            (p.name, p.kind, p.default) for p in expected.parameters.values()
        ], f"{implementation.__name__}.{name}{actual} != {expected}"


async def test_fake_geocoder_knows_real_cities() -> None:
    [paris] = await FakeGeocoder().search("paris")
    assert (paris.lat, paris.lon, paris.country_code) == (48.8566, 2.3522, "FR")
    [ny] = await FakeGeocoder().search("New York")
    assert ny.country_code == "US"
    assert len(KNOWN_CITIES) == 6


async def test_fake_geocoder_hashes_unknown_places_stably() -> None:
    first = await FakeGeocoder().search("Ulaanbaatar")
    second = await FakeGeocoder().search("  ulaanbaatar ")
    assert first == second
    assert first[0].name == "Ulaanbaatar"
    assert -90 <= first[0].lat <= 90
    assert await FakeGeocoder().search(" ") == []


async def test_fake_reverse() -> None:
    near = await FakeGeocoder().reverse(ports.GeoPoint(lat=27.70, lon=85.31))
    assert near is not None
    assert near.name == "Kathmandu"
    far = await FakeGeocoder().reverse(ports.GeoPoint(lat=0, lon=-30))
    assert far is not None
    assert far.name == "0.0000, -30.0000"


async def test_fake_autocomplete() -> None:
    suggestions = await FakeAutocomplete().suggest("po")
    assert [p.name for p in suggestions] == ["Pokhara"]
    assert await FakeAutocomplete().suggest("p") == []


async def test_fake_places_stay_inside_the_radius() -> None:
    places = await FakePlaces().nearby(
        KATHMANDU, categories=["museum", "cafe"], radius_m=2000, limit=12
    )
    assert len(places) == 12
    assert {p.category for p in places} == {"museum", "cafe"}
    assert all(haversine_m(KATHMANDU.lat, KATHMANDU.lon, p.lat, p.lon) <= 2000 for p in places)
    assert len({(p.lat, p.lon) for p in places}) == 12
    assert places == await FakePlaces().nearby(
        KATHMANDU, categories=["museum", "cafe"], radius_m=2000, limit=12
    )


async def test_fake_router() -> None:
    pokhara = ports.GeoPoint(lat=28.2096, lon=83.9856)
    walk = await FakeRouter().route([KATHMANDU, pokhara])
    drive = await FakeRouter().route([KATHMANDU, pokhara], profile="car")
    assert walk is not None
    assert drive is not None
    assert walk.distance_m == drive.distance_m > 140_000
    assert walk.duration_s > drive.duration_s
    assert walk.geometry == [(85.3240, 27.7172), (83.9856, 28.2096)]
    assert await FakeRouter().route([KATHMANDU]) is None


async def test_fake_weather() -> None:
    today = date(2026, 11, 5)
    days = await FakeWeather(today=today).daily(KATHMANDU, today, today + timedelta(days=20))
    assert len(days) == 21
    assert all(d.temp_min_c < d.temp_max_c for d in days)
    assert all(d.summary for d in days)
    assert [d.is_climate_estimate for d in days] == [False] * 15 + [True] * 6


async def test_fake_guides_and_photos() -> None:
    guide = await FakeGuides().guide("lisbon")
    assert guide is not None
    assert guide.destination == "Lisbon"
    assert {s.title for s in guide.sections} >= {"Understand", "See", "Eat"}
    assert await FakeGuides().guide("  ") is None

    fake_photos = FakePhotos()
    photos = await fake_photos.search("Lisbon Old Town", limit=3)
    assert photos[0].url == "https://picsum.photos/seed/lisbon-old-town-0/800/533"
    assert len({p.url for p in photos}) == 3
    await fake_photos.track_download(photos[0])
    assert fake_photos.tracked == [photos[0]]


async def test_memory_storage() -> None:
    storage = MemoryStorage()
    await storage.put("a/b.txt", b"hi", "text/plain")
    assert await storage.get("a/b.txt") == b"hi"
    assert await storage.download_url("a/b.txt", "b.txt") is None
    await storage.delete("a/b.txt")
    with pytest.raises(NotFound):
        await storage.get("a/b.txt")
