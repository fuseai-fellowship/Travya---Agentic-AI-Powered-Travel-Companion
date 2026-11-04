from typing import Any

import httpx
import pytest
import respx

from app.core.config import Settings
from app.integrations.geocoding.nominatim import NominatimGeocoder
from app.integrations.geocoding.photon import PhotonAutocomplete
from app.integrations.ports import GeoPoint

NOMINATIM_SEARCH = "https://nominatim.openstreetmap.org/search"
NOMINATIM_REVERSE = "https://nominatim.openstreetmap.org/reverse"
PHOTON = "https://photon.komoot.io/api"

KATHMANDU_SEARCH: list[dict[str, Any]] = [
    {
        "place_id": 8693468,
        "licence": "Data © OpenStreetMap contributors, ODbL 1.0. http://osm.org/copyright",
        "osm_type": "relation",
        "osm_id": 4583247,
        "lat": "27.708317",
        "lon": "85.3205817",
        "category": "boundary",
        "type": "administrative",
        "place_rank": 16,
        "importance": 0.7090510426,
        "addresstype": "city",
        "name": "Kathmandu",
        "display_name": "Kathmandu, Kathmandu Metropolitan City, Kathmandu, Bagmati Province, Nepal",
        "address": {
            "city": "Kathmandu",
            "county": "Kathmandu",
            "state": "Bagmati Province",
            "ISO3166-2-lvl4": "NP-P3",
            "country": "Nepal",
            "country_code": "np",
        },
        "boundingbox": ["27.6497000", "27.7539000", "85.2738000", "85.3696000"],
    },
    {
        "place_id": 8580020,
        "licence": "Data © OpenStreetMap contributors, ODbL 1.0. http://osm.org/copyright",
        "osm_type": "node",
        "osm_id": 2097181519,
        "lat": "27.6966",
        "lon": "85.3591",
        "category": "aeroway",
        "type": "aerodrome",
        "place_rank": 30,
        "importance": 0.41,
        "addresstype": "aeroway",
        "name": "Tribhuvan International Airport",
        "display_name": "Tribhuvan International Airport, Ring Road, Sinamangal, Kathmandu, Nepal",
        "address": {
            "aeroway": "Tribhuvan International Airport",
            "road": "Ring Road",
            "suburb": "Sinamangal",
            "city": "Kathmandu",
            "postcode": "44600",
            "country": "Nepal",
            "country_code": "np",
        },
        "boundingbox": ["27.6866", "27.7066", "85.3491", "85.3691"],
    },
]

EIFFEL_REVERSE: dict[str, Any] = {
    "place_id": 88066702,
    "licence": "Data © OpenStreetMap contributors, ODbL 1.0. http://osm.org/copyright",
    "osm_type": "way",
    "osm_id": 5013364,
    "lat": "48.8582599",
    "lon": "2.2945006",
    "category": "man_made",
    "type": "tower",
    "place_rank": 30,
    "importance": 0.6205937724,
    "addresstype": "man_made",
    "name": "Tour Eiffel",
    "display_name": "Tour Eiffel, 5, Avenue Anatole France, Gros-Caillou, Paris, 75007, France",
    "address": {
        "man_made": "Tour Eiffel",
        "house_number": "5",
        "road": "Avenue Anatole France",
        "suburb": "Gros-Caillou",
        "city": "Paris",
        "postcode": "75007",
        "country": "France",
        "country_code": "fr",
    },
}

PHOTON_LISBON: dict[str, Any] = {
    "type": "FeatureCollection",
    "features": [
        {
            "type": "Feature",
            "geometry": {"type": "Point", "coordinates": [-9.1365919, 38.7077507]},
            "properties": {
                "osm_type": "R",
                "osm_id": 5400890,
                "osm_key": "place",
                "osm_value": "city",
                "type": "city",
                "countrycode": "PT",
                "name": "Lisbon",
                "country": "Portugal",
                "state": "Lisbon",
                "extent": [-9.2298356, 38.7958538, -9.0866259, 38.6913994],
            },
        },
        {
            "type": "Feature",
            "geometry": {"type": "Point", "coordinates": [-9.14, 38.71]},
            "properties": {
                "osm_type": "N",
                "osm_id": 265958490,
                "osm_key": "place",
                "osm_value": "city",
                "type": "city",
                "countrycode": "PT",
                "name": "Lisbon",
                "country": "Portugal",
                "state": "Lisbon",
            },
        },
        {
            "type": "Feature",
            "geometry": {"type": "Point", "coordinates": [-9.1393, 38.7223]},
            "properties": {
                "osm_type": "W",
                "osm_id": 23110950,
                "osm_key": "highway",
                "osm_value": "residential",
                "type": "street",
                "countrycode": "PT",
                "street": "Rua de Lisboa",
                "postcode": "1000-001",
                "city": "Lisbon",
                "country": "Portugal",
            },
        },
        {
            "type": "Feature",
            "geometry": {"type": "Point", "coordinates": [1.0, 2.0]},
            "properties": {},
        },
    ],
}


async def test_nominatim_search_sends_policy_params_and_parses(
    http: httpx.AsyncClient, settings: Settings, respx_mock: respx.MockRouter
) -> None:
    route = respx_mock.get(NOMINATIM_SEARCH).respond(json=KATHMANDU_SEARCH)

    places = await NominatimGeocoder(http).search(" Kathmandu ", limit=2)

    request = route.calls.last.request
    assert request.headers["User-Agent"] == settings.HTTP_USER_AGENT
    assert dict(request.url.params) == {
        "format": "jsonv2",
        "addressdetails": "1",
        "accept-language": "en",
        "q": "Kathmandu",
        "limit": "2",
    }
    city, airport = places
    assert (city.name, city.lat, city.lon) == ("Kathmandu", 27.708317, 85.3205817)
    assert city.category == "city"
    assert city.country_code == "NP"
    assert city.osm_ref == "relation/4583247"
    assert city.source == "nominatim"
    assert city.address == "Kathmandu, Nepal"
    assert airport.osm_ref == "node/2097181519"
    assert airport.address == "Ring Road, Sinamangal, Kathmandu, 44600, Nepal"


async def test_nominatim_search_is_cached(
    http: httpx.AsyncClient, respx_mock: respx.MockRouter
) -> None:
    route = respx_mock.get(NOMINATIM_SEARCH).respond(json=KATHMANDU_SEARCH)
    geocoder = NominatimGeocoder(http)

    first = await geocoder.search("Kathmandu")
    second = await geocoder.search("kathmandu")

    assert route.call_count == 1
    assert first == second


async def test_nominatim_empty_results_are_not_cached(
    http: httpx.AsyncClient, respx_mock: respx.MockRouter
) -> None:
    route = respx_mock.get(NOMINATIM_SEARCH).respond(json=[])
    geocoder = NominatimGeocoder(http)

    assert await geocoder.search("Atlantis") == []
    assert await geocoder.search("Atlantis") == []
    assert route.call_count == 2


async def test_nominatim_blank_query_makes_no_request(
    http: httpx.AsyncClient, respx_mock: respx.MockRouter
) -> None:
    route = respx_mock.get(NOMINATIM_SEARCH).respond(json=[])
    assert await NominatimGeocoder(http).search("   ") == []
    assert not route.called


async def test_nominatim_reverse(http: httpx.AsyncClient, respx_mock: respx.MockRouter) -> None:
    route = respx_mock.get(NOMINATIM_REVERSE).respond(json=EIFFEL_REVERSE)

    place = await NominatimGeocoder(http).reverse(GeoPoint(lat=48.85826, lon=2.2945))

    params = route.calls.last.request.url.params
    assert (params["lat"], params["lon"], params["format"]) == ("48.85826", "2.2945", "jsonv2")
    assert place is not None
    assert place.name == "Tour Eiffel"
    assert place.osm_ref == "way/5013364"
    assert place.address == "5 Avenue Anatole France, Gros-Caillou, Paris, 75007, France"


async def test_nominatim_reverse_in_the_ocean_is_none(
    http: httpx.AsyncClient, respx_mock: respx.MockRouter
) -> None:
    respx_mock.get(NOMINATIM_REVERSE).respond(json={"error": "Unable to geocode"})
    assert await NominatimGeocoder(http).reverse(GeoPoint(lat=0, lon=-30)) is None


async def test_photon_suggest_with_bias(
    http: httpx.AsyncClient, respx_mock: respx.MockRouter
) -> None:
    route = respx_mock.get(PHOTON).respond(json=PHOTON_LISBON)

    places = await PhotonAutocomplete(http).suggest(
        "lisb", limit=5, near=GeoPoint(lat=38.71234, lon=-9.13987)
    )

    params = route.calls.last.request.url.params
    assert params["q"] == "lisb"
    assert params["limit"] == "5"
    assert params["lang"] == "en"
    assert (params["lat"], params["lon"], params["zoom"]) == ("38.71", "-9.14", "10")
    # the duplicate city node and the nameless feature are dropped
    assert [p.display_name for p in places] == [
        "Lisbon, Portugal",
        "Rua de Lisboa, Lisbon, Portugal",
    ]
    lisbon, street = places
    assert (lisbon.lat, lisbon.lon) == (38.7077507, -9.1365919)
    assert lisbon.osm_ref == "relation/5400890"
    assert lisbon.country_code == "PT"
    assert lisbon.category == "city"
    assert lisbon.source == "photon"
    assert street.address == "Rua de Lisboa, 1000-001, Lisbon, Portugal"


async def test_photon_without_bias_and_cache(
    http: httpx.AsyncClient, respx_mock: respx.MockRouter
) -> None:
    route = respx_mock.get(PHOTON).respond(json=PHOTON_LISBON)
    photon = PhotonAutocomplete(http)

    await photon.suggest("Lisbon")
    await photon.suggest("lisbon ")

    assert route.call_count == 1
    assert "lat" not in route.calls.last.request.url.params


@pytest.mark.parametrize("query", ["", " ", "l"])
async def test_photon_ignores_too_short_queries(
    http: httpx.AsyncClient, respx_mock: respx.MockRouter, query: str
) -> None:
    route = respx_mock.get(PHOTON).respond(json=PHOTON_LISBON)
    assert await PhotonAutocomplete(http).suggest(query) == []
    assert not route.called
