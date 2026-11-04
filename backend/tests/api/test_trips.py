import pytest
from httpx import AsyncClient

from tests.conftest import TRIP

pytestmark = pytest.mark.db


async def test_requires_authentication(anonymous: AsyncClient) -> None:
    response = await anonymous.get("/trips")
    assert response.status_code == 401
    assert response.headers["content-type"].startswith("application/problem+json")
    assert response.headers["www-authenticate"] == "Bearer"


async def test_health_is_public(anonymous: AsyncClient) -> None:
    assert (await anonymous.get("/health/live")).json() == {"status": "ok"}
    assert (await anonymous.get("/health/ready")).json() == {"status": "ok"}


async def test_create_geocodes_and_lists(alice: AsyncClient, trip: dict[str, object]) -> None:
    assert trip["latitude"] is not None
    assert trip["status"] == "draft"
    assert trip["cover_photo_url"]
    page = (await alice.get("/trips")).json()
    assert page["total"] == 1
    assert page["items"][0]["id"] == trip["id"]
    assert (await alice.get("/trips", params={"q": "valley"})).json()["total"] == 1
    assert (await alice.get("/trips", params={"q": "lisbon"})).json()["total"] == 0


@pytest.mark.parametrize(
    ("change", "message"),
    [
        ({"end_date": "2027-03-01"}, "end_date must be on or after start_date"),
        ({"end_date": "2027-05-30"}, "at most 21 days"),
        ({"currency": "usd"}, "String should match pattern"),
        ({"travelers": 0}, "greater than or equal to 1"),
    ],
)
async def test_validation_errors(
    alice: AsyncClient, change: dict[str, object], message: str
) -> None:
    response = await alice.post("/trips", json=TRIP | change)
    assert response.status_code == 422
    assert message in str(response.json()["errors"])


async def test_update_and_delete(alice: AsyncClient, trip: dict[str, object]) -> None:
    response = await alice.patch(
        f"/trips/{trip['id']}", json={"title": "Valley of temples", "travelers": 3}
    )
    assert response.json()["title"] == "Valley of temples"
    assert response.json()["travelers"] == 3
    bad = await alice.patch(f"/trips/{trip['id']}", json={"end_date": "2027-01-01"})
    assert bad.status_code == 422
    assert (await alice.delete(f"/trips/{trip['id']}")).status_code == 204
    assert (await alice.get(f"/trips/{trip['id']}")).status_code == 404


async def test_itinerary_crud_and_day_bounds(alice: AsyncClient, trip: dict[str, object]) -> None:
    base = f"/trips/{trip['id']}/itinerary"
    created = await alice.post(
        base, json={"day": "2027-03-11", "title": "Patan Durbar Square", "category": "sight"}
    )
    assert created.status_code == 201
    item = created.json()
    assert item["position"] == 0
    assert item["source"] == "user"
    second = (await alice.post(base, json={"day": "2027-03-11", "title": "Lunch"})).json()
    assert second["position"] == 1
    outside = await alice.post(base, json={"day": "2027-04-01", "title": "Too late"})
    assert outside.status_code == 422
    moved = await alice.patch(
        f"{base}/{item['id']}", json={"start_time": "09:30", "day": "2027-03-12"}
    )
    assert moved.json()["start_time"] == "09:30:00"
    assert [i["title"] for i in (await alice.get(base)).json()] == ["Lunch", "Patan Durbar Square"]
    assert (await alice.delete(f"{base}/{item['id']}")).status_code == 204
    assert len((await alice.get(base)).json()) == 1
