from datetime import date
from types import SimpleNamespace

from app.integrations.ports import Place
from app.services.planning import _normalise, _PlaceResolver


class Geocoder:
    def __init__(self, results: list[Place]) -> None:
        self.results = results
        self.queries: list[str] = []

    async def search(self, query: str, *, limit: int = 5) -> list[Place]:
        self.queries.append(query)
        return self.results


def _resolver(results: list[Place]) -> tuple[_PlaceResolver, Geocoder]:
    geocoder = Geocoder(results)
    trip = SimpleNamespace(
        destination="Pokhara, Nepal", latitude=28.21, longitude=83.99, start_date=date(2027, 1, 1)
    )
    places = [
        {"name": "Phewa Lake", "lat": 28.215, "lon": 83.945},
        {"name": "World Peace Pagoda", "lat": 28.2, "lon": 83.944},
    ]
    return _PlaceResolver(SimpleNamespace(geocoder=geocoder), trip, places), geocoder  # type: ignore[arg-type]


def test_normalise() -> None:
    assert _normalise("The Phewa Lake!") == "phewa lake"


async def test_uses_research_places_with_fuzzy_names() -> None:
    resolver, geocoder = _resolver([])
    assert await resolver.locate("Phewa Lake") == (28.215, 83.945)
    assert await resolver.locate("Boating on Phewa Lake") == (28.215, 83.945)
    assert await resolver.locate(None) == (None, None)
    assert geocoder.queries == []


async def test_geocodes_nearby_matches_only() -> None:
    far = Place(
        name="Sarangkot", display_name="Sarangkot, Peru", lat=-12.0, lon=-77.0, source="nominatim"
    )
    near = Place(
        name="Sarangkot",
        display_name="Sarangkot, Nepal",
        lat=28.244,
        lon=83.948,
        source="nominatim",
    )
    resolver, geocoder = _resolver([far, near])
    assert await resolver.locate("Sarangkot Viewpoint") == (28.244, 83.948)
    assert geocoder.queries == ["Sarangkot Viewpoint, Pokhara"]
    assert await resolver.locate("Sarangkot Viewpoint") == (28.244, 83.948)
    assert len(geocoder.queries) == 1
