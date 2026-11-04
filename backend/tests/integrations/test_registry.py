from pathlib import Path

import httpx
import pytest

from app.core.config import Settings
from app.integrations import fakes
from app.integrations.geocoding.nominatim import NominatimGeocoder
from app.integrations.offers.sample import SampleOffers
from app.integrations.photos import FallbackPhotos
from app.integrations.photos.wikimedia import WikimediaPhotos
from app.integrations.registry import build_integrations
from app.integrations.routing import FallbackRouter
from app.integrations.routing.osrm import OsrmRouter
from app.integrations.storage.gcs import GcsStorage
from app.integrations.storage.local import LocalStorage
from app.integrations.weather.open_meteo import OpenMeteoWeather


def test_offline_uses_fakes_everywhere(http: httpx.AsyncClient) -> None:
    integrations = build_integrations(Settings(OFFLINE_INTEGRATIONS=True), http)
    assert isinstance(integrations.geocoder, fakes.FakeGeocoder)
    assert isinstance(integrations.autocomplete, fakes.FakeAutocomplete)
    assert isinstance(integrations.places, fakes.FakePlaces)
    assert isinstance(integrations.router, fakes.FakeRouter)
    assert isinstance(integrations.weather, fakes.FakeWeather)
    assert isinstance(integrations.guides, fakes.FakeGuides)
    assert isinstance(integrations.photos, fakes.FakePhotos)
    assert isinstance(integrations.offers, SampleOffers)
    assert isinstance(integrations.storage, fakes.MemoryStorage)


def test_keyless_online_uses_open_services(http: httpx.AsyncClient, tmp_path: Path) -> None:
    settings = Settings(
        OFFLINE_INTEGRATIONS=False,
        ORS_API_KEY=None,
        UNSPLASH_ACCESS_KEY=None,
        STORAGE_BACKEND="local",
        LOCAL_STORAGE_DIR=str(tmp_path),
    )
    integrations = build_integrations(settings, http)
    assert isinstance(integrations.geocoder, NominatimGeocoder)
    assert isinstance(integrations.router, OsrmRouter)
    assert isinstance(integrations.weather, OpenMeteoWeather)
    assert isinstance(integrations.photos, WikimediaPhotos)
    assert isinstance(integrations.offers, SampleOffers)
    assert isinstance(integrations.storage, LocalStorage)


def test_keys_enable_ors_unsplash_and_gcs(http: httpx.AsyncClient) -> None:
    settings = Settings(
        OFFLINE_INTEGRATIONS=False,
        ORS_API_KEY="ors",
        UNSPLASH_ACCESS_KEY="unsplash",
        STORAGE_BACKEND="gcs",
        GCS_BUCKET="travya-docs",
    )
    integrations = build_integrations(settings, http)
    assert isinstance(integrations.router, FallbackRouter)
    assert isinstance(integrations.photos, FallbackPhotos)
    assert isinstance(integrations.storage, GcsStorage)


def test_gcs_without_bucket_is_a_config_error(http: httpx.AsyncClient) -> None:
    settings = Settings(OFFLINE_INTEGRATIONS=False, STORAGE_BACKEND="gcs", GCS_BUCKET=None)
    with pytest.raises(ValueError, match="GCS_BUCKET"):
        build_integrations(settings, http)
