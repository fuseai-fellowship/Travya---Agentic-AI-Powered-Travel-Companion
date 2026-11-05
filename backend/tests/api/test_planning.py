"""The full agent flow offline: research scouts → scripted planner → persisted itinerary → HITL booking."""

import json

import pytest
from httpx import AsyncClient

pytestmark = pytest.mark.db


def parse_sse(body: str) -> list[dict[str, object]]:
    events = []
    for block in body.split("\r\n\r\n" if "\r\n\r\n" in body else "\n\n"):
        data = [line[5:].strip() for line in block.splitlines() if line.startswith("data:")]
        if data:
            events.append(json.loads("".join(data)))
    return events


async def test_plan_stream_persists_itinerary_and_quotes(
    alice: AsyncClient, trip: dict[str, object]
) -> None:
    response = await alice.post(
        f"/trips/{trip['id']}/plan", json={"instructions": "one slow morning"}
    )
    assert response.status_code == 200
    assert response.headers["content-type"].startswith("text/event-stream")
    events = parse_sse(response.text)
    agents = {e["agent"] for e in events}
    assert {"weather_scout", "places_scout", "guide_scout", "offers_scout", "planner"} <= agents
    assert events[-1]["kind"] == "done"

    detail = (await alice.get(f"/trips/{trip['id']}")).json()
    assert detail["status"] == "planned"
    assert len(detail["plan"]["days"]) == 3
    assert any(
        s["url"] == "https://www.openstreetmap.org/copyright" for s in detail["plan"]["sources"]
    )

    items = (await alice.get(f"/trips/{trip['id']}/itinerary")).json()
    assert items
    assert {i["source"] for i in items} == {"agent"}
    assert all("2027-03-10" <= i["day"] <= "2027-03-12" for i in items)

    trip_map = (await alice.get(f"/trips/{trip['id']}/map")).json()
    kinds = {f["properties"]["kind"] for f in trip_map["features"]}
    assert "stop" in kinds
    assert trip_map["attribution"] == "© OpenStreetMap contributors"

    bookings = (await alice.get(f"/trips/{trip['id']}/bookings")).json()
    assert {b["kind"] for b in bookings} == {"flight", "hotel"}
    assert all(b["status"] == "quoted" and b["is_simulated"] for b in bookings)


async def test_booking_needs_explicit_confirmation(
    alice: AsyncClient, trip: dict[str, object]
) -> None:
    await alice.post(f"/trips/{trip['id']}/plan", json={})
    bookings = (await alice.get(f"/trips/{trip['id']}/bookings")).json()
    hotels = [b for b in bookings if b["kind"] == "hotel"]
    chosen = hotels[0]

    confirmed = (await alice.post(f"/trips/{trip['id']}/bookings/{chosen['id']}/confirm")).json()
    assert confirmed["status"] == "confirmed"
    assert confirmed["confirmation_code"].startswith("SIM-")
    again = await alice.post(f"/trips/{trip['id']}/bookings/{chosen['id']}/confirm")
    assert again.status_code == 409

    after = {
        b["id"]: b["status"] for b in (await alice.get(f"/trips/{trip['id']}/bookings")).json()
    }
    assert all(after[h["id"]] == "cancelled" for h in hotels[1:])
    assert (await alice.get(f"/trips/{trip['id']}")).json()["status"] == "booked"

    # Re-planning keeps confirmed bookings and user-added items.
    await alice.post(
        f"/trips/{trip['id']}/itinerary", json={"day": "2027-03-10", "title": "My own plan"}
    )
    await alice.post(f"/trips/{trip['id']}/plan", json={})
    after_replan = (await alice.get(f"/trips/{trip['id']}/bookings")).json()
    assert any(b["id"] == chosen["id"] and b["status"] == "confirmed" for b in after_replan)
    titles = [i["title"] for i in (await alice.get(f"/trips/{trip['id']}/itinerary")).json()]
    assert "My own plan" in titles
    assert (await alice.get(f"/trips/{trip['id']}")).json()["status"] == "booked"


async def test_plan_rate_limit(
    alice: AsyncClient, trip: dict[str, object], monkeypatch: pytest.MonkeyPatch
) -> None:
    from app.core.config import settings

    monkeypatch.setattr(settings, "LLM_DAILY_REQUEST_BUDGET", 1)
    first = await alice.post(f"/trips/{trip['id']}/plan", json={})
    assert first.status_code == 200
    exhausted = await alice.post(f"/trips/{trip['id']}/plan", json={})
    assert exhausted.status_code == 503
    assert exhausted.json()["title"] == "Demo limit reached"


async def test_photos_and_weather(alice: AsyncClient, trip: dict[str, object]) -> None:
    photos = (await alice.post(f"/trips/{trip['id']}/photos/refresh")).json()
    assert photos
    assert all(p["author_name"] and p["source_url"] for p in photos)
    weather = (await alice.get(f"/trips/{trip['id']}/weather")).json()
    assert [w["day"] for w in weather] == ["2027-03-10", "2027-03-11", "2027-03-12"]
