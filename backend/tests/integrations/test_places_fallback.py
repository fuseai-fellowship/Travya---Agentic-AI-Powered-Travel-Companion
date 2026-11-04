import httpx
import pytest
import respx

from app.core.errors import UpstreamUnavailable
from app.integrations.offers.sample import SampleOffers
from app.integrations.places import FallbackPlaces
from app.integrations.places.wikipedia import API_URL, WikipediaPlaces
from app.integrations.ports import GeoPoint, Place, PoiCategory

CENTER = GeoPoint(lat=28.2095, lon=83.9914)
GEOSEARCH = {
    "query": {
        "geosearch": [
            {"pageid": 1, "title": "Phewa Lake", "lat": 28.215, "lon": 83.945},
            {"pageid": 2, "title": "Kaski District", "lat": 28.3, "lon": 83.9},
            {"pageid": 3, "title": "World Peace Pagoda", "lat": 28.2, "lon": 83.944},
        ]
    }
}


class Stub:
    def __init__(self, result: list[Place] | Exception) -> None:
        self.result = result
        self.calls = 0

    async def nearby(
        self,
        center: GeoPoint,
        *,
        categories: list[PoiCategory],
        radius_m: int = 3000,
        limit: int = 30,
    ) -> list[Place]:
        self.calls += 1
        if isinstance(self.result, Exception):
            raise self.result
        return self.result


PLACE = Place(name="Sarangkot", display_name="Sarangkot", lat=28.24, lon=83.95, source="osm")


@respx.mock
async def test_wikipedia_geosearch_skips_areas(http: httpx.AsyncClient) -> None:
    route = respx.get(API_URL).mock(return_value=httpx.Response(200, json=GEOSEARCH))
    places = await WikipediaPlaces(http).nearby(CENTER, categories=["attraction"], radius_m=4000)
    assert [p.name for p in places] == ["Phewa Lake", "World Peace Pagoda"]
    assert route.calls[0].request.url.params["gscoord"] == "28.2095|83.9914"
    assert await WikipediaPlaces(http).nearby(CENTER, categories=["restaurant"]) == []


@pytest.mark.parametrize("failure", [UpstreamUnavailable("down"), TimeoutError()])
async def test_fallback_on_failure(failure: Exception) -> None:
    primary, fallback = Stub(failure), Stub([PLACE])
    places = await FallbackPlaces(primary, fallback).nearby(CENTER, categories=["attraction"])
    assert places == [PLACE]
    assert fallback.calls == 1


async def test_fallback_on_empty_and_primary_preferred() -> None:
    empty, fallback = Stub([]), Stub([PLACE])
    assert await FallbackPlaces(empty, fallback).nearby(CENTER, categories=["museum"]) == [PLACE]
    primary, unused = Stub([PLACE]), Stub([])
    assert await FallbackPlaces(primary, unused).nearby(CENTER, categories=["museum"]) == [PLACE]
    assert unused.calls == 0


async def test_sample_fares_scale_with_distance() -> None:
    from datetime import date

    offers = SampleOffers()
    args = {
        "origin": "A",
        "destination": "B",
        "depart": date(2027, 1, 5),
        "return_date": None,
        "travelers": 1,
        "currency": "USD",
    }
    short = await offers.flights(**args, distance_km=200)
    long = await offers.flights(**args, distance_km=9000)
    assert max(o.amount for o in short) < min(o.amount for o in long)
    assert short[0].details["duration_minutes"] < long[0].details["duration_minutes"]
