"""Wires each port to its adapter from settings: real services online, fakes offline."""

from dataclasses import dataclass

import httpx

from app.core.config import Settings
from app.integrations.fakes import (
    FakeAutocomplete,
    FakeGeocoder,
    FakeGuides,
    FakePhotos,
    FakePlaces,
    FakeRouter,
    FakeWeather,
    MemoryStorage,
)
from app.integrations.geocoding.nominatim import NominatimGeocoder
from app.integrations.geocoding.photon import PhotonAutocomplete
from app.integrations.guides.wikivoyage import WikivoyageGuides
from app.integrations.offers.sample import SampleOffers
from app.integrations.photos import FallbackPhotos
from app.integrations.photos.unsplash import UnsplashPhotos
from app.integrations.photos.wikimedia import WikimediaPhotos
from app.integrations.places import FallbackPlaces
from app.integrations.places.overpass import OverpassPlaces
from app.integrations.places.wikipedia import WikipediaPlaces
from app.integrations.ports import (
    Autocomplete,
    Geocoder,
    GuideProvider,
    ObjectStorage,
    OffersProvider,
    PhotoProvider,
    PlacesSearch,
    Router,
    WeatherProvider,
)
from app.integrations.routing import FallbackRouter
from app.integrations.routing.ors import OrsRouter
from app.integrations.routing.osrm import OsrmRouter
from app.integrations.storage.gcs import GcsStorage
from app.integrations.storage.local import LocalStorage
from app.integrations.weather.open_meteo import OpenMeteoWeather


@dataclass(frozen=True)
class Integrations:
    geocoder: Geocoder
    autocomplete: Autocomplete
    places: PlacesSearch
    router: Router
    weather: WeatherProvider
    guides: GuideProvider
    photos: PhotoProvider
    offers: OffersProvider
    storage: ObjectStorage


def build_integrations(settings: Settings, http: httpx.AsyncClient) -> Integrations:
    if settings.OFFLINE_INTEGRATIONS:
        return Integrations(
            geocoder=FakeGeocoder(),
            autocomplete=FakeAutocomplete(),
            places=FakePlaces(),
            router=FakeRouter(),
            weather=FakeWeather(),
            guides=FakeGuides(),
            photos=FakePhotos(),
            offers=SampleOffers(),
            storage=MemoryStorage(),
        )

    router: Router = OsrmRouter(http)
    if settings.ORS_API_KEY:
        router = FallbackRouter(OrsRouter(http, settings.ORS_API_KEY.get_secret_value()), router)
    photos: PhotoProvider = WikimediaPhotos(http)
    if settings.UNSPLASH_ACCESS_KEY:
        photos = FallbackPhotos(
            UnsplashPhotos(http, settings.UNSPLASH_ACCESS_KEY.get_secret_value()), photos
        )
    return Integrations(
        geocoder=NominatimGeocoder(http),
        autocomplete=PhotonAutocomplete(http),
        places=FallbackPlaces(OverpassPlaces(http), WikipediaPlaces(http)),
        router=router,
        weather=OpenMeteoWeather(http),
        guides=WikivoyageGuides(http),
        photos=photos,
        offers=SampleOffers(),
        storage=_storage(settings),
    )


def _storage(settings: Settings) -> ObjectStorage:
    if settings.STORAGE_BACKEND == "gcs":
        if not settings.GCS_BUCKET:
            raise ValueError("STORAGE_BACKEND=gcs needs GCS_BUCKET")
        return GcsStorage(settings.GCS_BUCKET)
    return LocalStorage(settings.LOCAL_STORAGE_DIR)
