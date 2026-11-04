"""Smoke tests against the real services: `RUN_LIVE=1 uv run pytest -m live tests/integrations`."""

import os
from collections.abc import AsyncIterator
from datetime import UTC, datetime, timedelta

import httpx
import pytest

from app.core.config import Settings
from app.integrations.geocoding.nominatim import NominatimGeocoder
from app.integrations.geocoding.photon import PhotonAutocomplete
from app.integrations.guides.wikivoyage import WikivoyageGuides
from app.integrations.http import create_http_client
from app.integrations.photos.unsplash import UnsplashPhotos
from app.integrations.photos.wikimedia import WikimediaPhotos
from app.integrations.places.overpass import OverpassPlaces
from app.integrations.ports import GeoPoint
from app.integrations.routing.ors import OrsRouter
from app.integrations.routing.osrm import OsrmRouter
from app.integrations.storage.gcs import GcsStorage
from app.integrations.weather.open_meteo import OpenMeteoWeather

pytestmark = [
    pytest.mark.live,
    pytest.mark.skipif(
        os.environ.get("RUN_LIVE") != "1", reason="set RUN_LIVE=1 to call real services"
    ),
]

LIVE = Settings()
KATHMANDU = GeoPoint(lat=27.7172, lon=85.3240)
SWAYAMBHU = GeoPoint(lat=27.7149, lon=85.2903)


@pytest.fixture
async def live_http() -> AsyncIterator[httpx.AsyncClient]:
    async with create_http_client(LIVE) as client:
        yield client


async def test_nominatim(live_http: httpx.AsyncClient) -> None:
    places = await NominatimGeocoder(live_http).search("Kathmandu", limit=1)
    assert places
    assert places[0].country_code == "NP"


async def test_photon(live_http: httpx.AsyncClient) -> None:
    places = await PhotonAutocomplete(live_http).suggest("Pokha", near=KATHMANDU)
    assert any(p.name == "Pokhara" for p in places)


async def test_overpass(live_http: httpx.AsyncClient) -> None:
    places = await OverpassPlaces(live_http).nearby(KATHMANDU, categories=["religious"], limit=5)
    assert places
    assert all(p.osm_ref for p in places)


async def test_osrm(live_http: httpx.AsyncClient) -> None:
    route = await OsrmRouter(live_http).route([KATHMANDU, SWAYAMBHU])
    assert route is not None
    assert 2_000 < route.distance_m < 10_000


@pytest.mark.skipif(not LIVE.ORS_API_KEY, reason="ORS_API_KEY is not set")
async def test_openrouteservice(live_http: httpx.AsyncClient) -> None:
    assert LIVE.ORS_API_KEY is not None
    route = await OrsRouter(live_http, LIVE.ORS_API_KEY.get_secret_value()).route(
        [KATHMANDU, SWAYAMBHU]
    )
    assert route is not None
    assert route.geometry


async def test_open_meteo(live_http: httpx.AsyncClient) -> None:
    today = datetime.now(UTC).date()
    days = await OpenMeteoWeather(live_http).daily(KATHMANDU, today, today + timedelta(days=20))
    assert len(days) == 21
    assert days[-1].is_climate_estimate


async def test_wikivoyage(live_http: httpx.AsyncClient) -> None:
    guide = await WikivoyageGuides(live_http).guide("Kathmandu")
    assert guide is not None
    assert guide.source == "wikivoyage"
    assert guide.sections


async def test_wikimedia(live_http: httpx.AsyncClient) -> None:
    photos = await WikimediaPhotos(live_http).search("Boudhanath", limit=2)
    assert photos
    assert photos[0].source_url.startswith("https://commons.wikimedia.org/")


@pytest.mark.skipif(not LIVE.UNSPLASH_ACCESS_KEY, reason="UNSPLASH_ACCESS_KEY is not set")
async def test_unsplash(live_http: httpx.AsyncClient) -> None:
    assert LIVE.UNSPLASH_ACCESS_KEY is not None
    unsplash = UnsplashPhotos(live_http, LIVE.UNSPLASH_ACCESS_KEY.get_secret_value())
    photos = await unsplash.search("Kathmandu", limit=1)
    assert photos
    await unsplash.track_download(photos[0])


@pytest.mark.skipif(not LIVE.GCS_BUCKET, reason="GCS_BUCKET is not set")
async def test_gcs() -> None:
    assert LIVE.GCS_BUCKET is not None
    storage = GcsStorage(LIVE.GCS_BUCKET)
    key = f"live-tests/{datetime.now(UTC):%Y%m%dT%H%M%S}.txt"
    await storage.put(key, b"travya", "text/plain")
    try:
        assert await storage.get(key) == b"travya"
        await storage.download_url(key, "check.txt")
    finally:
        await storage.delete(key)
