import asyncio
from datetime import date
from decimal import Decimal
from types import SimpleNamespace

from app.integrations.ports import GeoPoint, Place
from app.services.planning import _money, _normalise, _PlaceResolver


class Autocomplete:
    def __init__(self, results: list[Place], fail: set[str] | None = None) -> None:
        self.results = results
        self.fail = fail or set()
        self.queries: list[str] = []
        self.near: list[GeoPoint | None] = []

    async def suggest(
        self, query: str, *, limit: int = 6, near: GeoPoint | None = None
    ) -> list[Place]:
        self.queries.append(query)
        self.near.append(near)
        if any(name in query for name in self.fail):
            raise RuntimeError("upstream down")
        return self.results


def _resolver(
    results: list[Place], fail: set[str] | None = None
) -> tuple[_PlaceResolver, Autocomplete]:
    autocomplete = Autocomplete(results, fail)
    trip = SimpleNamespace(
        destination="Pokhara, Nepal", latitude=28.21, longitude=83.99, start_date=date(2027, 1, 1)
    )
    places = [
        {"name": "Phewa Lake", "lat": 28.215, "lon": 83.945},
        {"name": "World Peace Pagoda", "lat": 28.2, "lon": 83.944},
        {"name": "Durbar Square", "lat": 27.704, "lon": 85.307},
        {"name": "Bhaktapur Durbar Square", "lat": 27.672, "lon": 85.428},
    ]
    resolver = _PlaceResolver(SimpleNamespace(autocomplete=autocomplete), trip, places)  # type: ignore[arg-type]
    return resolver, autocomplete


NEAR = Place(
    name="Sarangkot", display_name="Sarangkot, Nepal", lat=28.244, lon=83.948, source="photon"
)
FAR = Place(name="Sarangkot", display_name="Sarangkot, Peru", lat=-12.0, lon=-77.0, source="photon")


def test_normalise() -> None:
    assert _normalise("The Phewa Lake!") == "phewa lake"


async def test_uses_research_places_with_fuzzy_names() -> None:
    resolver, autocomplete = _resolver([])
    await resolver.resolve(["Phewa Lake", "Boating on Phewa Lake", None])
    assert resolver.locate("Phewa Lake") == (28.215, 83.945)
    assert resolver.locate("Boating on Phewa Lake") == (28.215, 83.945)
    assert resolver.locate(None) == (None, None)
    assert autocomplete.queries == []


async def test_prefers_the_most_specific_research_match() -> None:
    resolver, _ = _resolver([])
    assert resolver.locate("Sunset at Bhaktapur Durbar Square") == (27.672, 85.428)


async def test_looks_up_unknown_places_near_the_trip_once() -> None:
    resolver, autocomplete = _resolver([FAR, NEAR])
    await resolver.resolve(["Sarangkot Viewpoint", "Sarangkot Viewpoint"])
    assert resolver.locate("Sarangkot Viewpoint") == (28.244, 83.948)
    assert autocomplete.queries == ["Sarangkot Viewpoint, Pokhara"]
    assert autocomplete.near == [GeoPoint(lat=28.21, lon=83.99)]


async def test_failed_or_far_lookups_leave_the_stop_unplaced() -> None:
    resolver, _ = _resolver([FAR], fail={"Begnas"})
    await resolver.resolve(["Begnas Lake", "Sarangkot Viewpoint"])
    assert resolver.locate("Begnas Lake") == (None, None)
    assert resolver.locate("Sarangkot Viewpoint") == (None, None)


async def test_lookups_are_bounded_in_number_and_time() -> None:
    resolver, autocomplete = _resolver([NEAR])
    await resolver.resolve([f"Unknown place {i}" for i in range(40)])
    assert len(autocomplete.queries) == _PlaceResolver.MAX_LOOKUPS

    class Slow(Autocomplete):
        async def suggest(
            self, query: str, *, limit: int = 6, near: GeoPoint | None = None
        ) -> list[Place]:
            await asyncio.sleep(10)
            return []

    slow, _ = _resolver([])
    slow.integrations = SimpleNamespace(autocomplete=Slow([]))  # type: ignore[assignment]
    slow.BUDGET_S = 0.05
    await slow.resolve(["Begnas Lake"])
    assert slow.locate("Begnas Lake") == (None, None)


def test_money_is_clamped_to_the_column() -> None:
    assert _money(-5) == Decimal("0.00")
    assert _money(12.346) == Decimal("12.35")
    assert _money(1e13) is None
    assert _money(None) is None
