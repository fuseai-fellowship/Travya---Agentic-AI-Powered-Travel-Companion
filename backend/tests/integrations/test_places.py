from typing import Any
from urllib.parse import parse_qs

import httpx
import pytest
import respx

from app.core.errors import UpstreamUnavailable
from app.integrations.places.overpass import OverpassPlaces, build_query
from app.integrations.ports import GeoPoint

OVERPASS = "https://overpass-api.de/api/interpreter"
PARIS = GeoPoint(lat=48.8566, lon=2.3522)

OVERPASS_PARIS: dict[str, Any] = {
    "version": 0.6,
    "generator": "Overpass API 0.7.62.5 1bd436f1",
    "osm3s": {"timestamp_osm_base": "2026-11-04T10:00:00Z", "copyright": "ODbL"},
    "elements": [
        {
            "type": "node",
            "id": 1001,
            "lat": 48.8570,
            "lon": 2.3530,
            "tags": {"amenity": "cafe", "name": "Café de la Place"},
        },
        {
            "type": "way",
            "id": 2002,
            "center": {"lat": 48.8606, "lon": 2.3376},
            "nodes": [1, 2, 3],
            "tags": {
                "tourism": "museum",
                "name": "Musée du Louvre",
                "name:en": "Louvre Museum",
                "wikidata": "Q19675",
                "wikipedia": "fr:Musée du Louvre",
                "opening_hours": "Mo,Th,Sa,Su 09:00-18:00; We,Fr 09:00-21:00",
                "website": "https://www.louvre.fr/",
                "addr:street": "Rue de Rivoli",
                "addr:city": "Paris",
            },
        },
        {
            "type": "node",
            "id": 1003,
            "lat": 48.8607,
            "lon": 2.3377,
            "tags": {"tourism": "museum", "name": "Louvre Museum"},
        },
        {
            "type": "node",
            "id": 1004,
            "lat": 48.8530,
            "lon": 2.3499,
            "tags": {"tourism": "museum", "name": "Musée de Cluny"},
        },
        {"type": "node", "id": 1005, "lat": 48.8566, "lon": 2.3522, "tags": {"amenity": "cafe"}},
        {
            "type": "node",
            "id": 1006,
            "lat": 48.8550,
            "lon": 2.3600,
            "tags": {"amenity": "cafe", "name": "Le Petit Café", "wikidata": "Q1"},
        },
        {
            "type": "relation",
            "id": 3007,
            "center": {"lat": 48.8530, "lon": 2.3500},
            "members": [],
            "tags": {"amenity": "restaurant", "name": "Not requested"},
        },
    ],
}
# the response repeats notable elements: they are output once on their own, then with the rest
OVERPASS_PARIS["elements"] = [
    *(e for e in OVERPASS_PARIS["elements"] if "wikidata" in e["tags"]),
    *OVERPASS_PARIS["elements"],
]


def _sent_query(request: httpx.Request) -> str:
    return parse_qs(request.content.decode())["data"][0]


def test_query_groups_tags_and_uses_around_and_center() -> None:
    query = build_query(48.8566, 2.3522, ("hotel", "museum", "nightlife"), 1500, max_elements=120)
    assert query.startswith("[out:json][timeout:25];(")
    assert 'nwr["tourism"~"^(gallery|guest_house|hostel|hotel|museum)$"]["name"]' in query
    assert 'nwr["amenity"~"^(bar|nightclub|pub)$"]["name"]' in query
    assert query.count("(around:1500,48.8566,2.3522)") == 2
    assert query.endswith(")->.poi;nwr.poi[wikidata];out center 120;.poi out center 120;")


async def test_nearby_posts_query_and_selects_places(
    http: httpx.AsyncClient, respx_mock: respx.MockRouter
) -> None:
    route = respx_mock.post(OVERPASS).respond(json=OVERPASS_PARIS)

    places = await OverpassPlaces(http).nearby(
        PARIS, categories=["museum", "cafe"], radius_m=2000, limit=10
    )

    request = route.calls.last.request
    # the client waits longer than the server-side query timeout
    assert request.extensions["timeout"]["read"] == 35
    query = _sent_query(request)
    assert "(around:2000,48.8566,2.3522)" in query
    assert 'nwr["amenity"~"^(cafe)$"]["name"]' in query
    # notable (wiki-tagged) first in each category, categories interleaved, duplicates and unnamed dropped
    assert [p.name for p in places] == [
        "Le Petit Café",
        "Louvre Museum",
        "Café de la Place",
        "Musée de Cluny",
    ]
    louvre = places[1]
    assert louvre.osm_ref == "way/2002"
    assert (louvre.lat, louvre.lon) == (48.8606, 2.3376)
    assert louvre.category == "museum"
    assert louvre.website == "https://www.louvre.fr/"
    assert louvre.opening_hours is not None
    assert louvre.address == "Rue de Rivoli, Paris"
    assert louvre.source == "overpass"


async def test_nearby_caps_to_limit_and_caches(
    http: httpx.AsyncClient, respx_mock: respx.MockRouter
) -> None:
    route = respx_mock.post(OVERPASS).respond(json=OVERPASS_PARIS)
    overpass = OverpassPlaces(http)

    first = await overpass.nearby(PARIS, categories=["cafe", "museum"], limit=2)
    again = await overpass.nearby(PARIS, categories=["museum", "cafe"], limit=2)

    assert len(first) == 2
    assert first == again
    assert route.call_count == 1


async def test_nearby_without_categories_makes_no_request(
    http: httpx.AsyncClient, respx_mock: respx.MockRouter
) -> None:
    route = respx_mock.post(OVERPASS).respond(json=OVERPASS_PARIS)
    assert await OverpassPlaces(http).nearby(PARIS, categories=[]) == []
    assert not route.called


async def test_overpass_runtime_error_is_upstream_unavailable(
    http: httpx.AsyncClient, respx_mock: respx.MockRouter
) -> None:
    respx_mock.post(OVERPASS).respond(
        json={
            "elements": [],
            "remark": 'runtime error: Query timed out in "query" at line 1 after 26 seconds.',
        }
    )
    with pytest.raises(UpstreamUnavailable, match="timed out"):
        await OverpassPlaces(http).nearby(PARIS, categories=["park"])


async def test_overpass_retries_when_busy(
    http: httpx.AsyncClient, respx_mock: respx.MockRouter, sleeps: list[float]
) -> None:
    route = respx_mock.post(OVERPASS).mock(
        side_effect=[httpx.Response(429), httpx.Response(200, json=OVERPASS_PARIS)]
    )
    assert await OverpassPlaces(http).nearby(PARIS, categories=["museum"])
    assert route.call_count == 2
