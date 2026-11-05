"""The full agent flow offline: research scouts → scripted planner → persisted itinerary → HITL booking."""

import json
import uuid
from typing import Any

import pytest
from httpx import AsyncClient
from sqlalchemy import text

from app.core.db import engine

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
    assert any(
        (e["agent"], e["kind"], e["message"]) == ("travya", "progress", "Placing stops on the map")
        for e in events
    )
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
    # One confirmed stay per trip: a new quote cannot be confirmed alongside it.
    fresh = next(b for b in after_replan if b["kind"] == "hotel" and b["status"] == "quoted")
    second = await alice.post(f"/trips/{trip['id']}/bookings/{fresh['id']}/confirm")
    assert second.status_code == 409
    assert "already confirmed" in second.json()["detail"]
    titles = [i["title"] for i in (await alice.get(f"/trips/{trip['id']}/itinerary")).json()]
    assert "My own plan" in titles
    assert (await alice.get(f"/trips/{trip['id']}")).json()["status"] == "booked"


async def test_spent_daily_budget_blocks_new_runs(
    alice: AsyncClient, trip: dict[str, object], monkeypatch: pytest.MonkeyPatch
) -> None:
    from app.core.config import settings

    monkeypatch.setattr(settings, "LLM_DAILY_REQUEST_BUDGET", 0)
    exhausted = await alice.post(f"/trips/{trip['id']}/plan", json={})
    assert exhausted.status_code == 503
    assert exhausted.json()["title"] == "Demo limit reached"
    assert (await alice.get(f"/trips/{trip['id']}")).json()["status"] == "draft"
    conversation = (await alice.post("/conversations", json={})).json()
    chat = await alice.post(
        f"/conversations/{conversation['id']}/messages", json={"content": "Hello"}
    )
    assert chat.status_code == 503
    assert chat.json()["title"] == "Demo limit reached"
    usage = (await alice.get("/me/usage")).json()
    assert usage == {
        "llm_runs_remaining_today": 0,
        "llm_calls_remaining_today": 0,
        "llm_calls_per_day": 0,
    }


async def test_plan_rate_limit(
    alice: AsyncClient, trip: dict[str, object], monkeypatch: pytest.MonkeyPatch
) -> None:
    from app.core.config import settings

    monkeypatch.setattr(settings, "RATE_LIMIT_PLAN", "1/hour")
    first = await alice.post(f"/trips/{trip['id']}/plan", json={})
    assert parse_sse(first.text)[-1]["kind"] == "done"
    limited = await alice.post(f"/trips/{trip['id']}/plan", json={})
    assert limited.status_code == 429
    assert int(limited.headers["retry-after"]) > 0


async def test_photos_and_weather(alice: AsyncClient, trip: dict[str, object]) -> None:
    photos = (await alice.post(f"/trips/{trip['id']}/photos/refresh")).json()
    assert photos
    assert all(p["author_name"] and p["source_url"] for p in photos)
    weather = (await alice.get(f"/trips/{trip['id']}/weather")).json()
    assert [w["day"] for w in weather] == ["2027-03-10", "2027-03-11", "2027-03-12"]


async def _set_planning(trip_id: object, minutes_ago: int) -> None:
    async with engine.begin() as connection:
        await connection.execute(
            text(
                "UPDATE trips SET status = 'planning', "
                "planning_started_at = now() - make_interval(mins => :minutes) WHERE id = :id"
            ),
            {"id": uuid.UUID(str(trip_id)), "minutes": minutes_ago},
        )


async def test_one_planning_run_per_trip(alice: AsyncClient, trip: dict[str, object]) -> None:
    await _set_planning(trip["id"], 1)
    busy = await alice.post(f"/trips/{trip['id']}/plan", json={})
    assert busy.status_code == 409
    assert (await alice.get(f"/trips/{trip['id']}")).json()["status"] == "planning"

    # A run that has been "planning" for longer than any run can take has died.
    await _set_planning(trip["id"], 11)
    assert (await alice.get(f"/trips/{trip['id']}")).json()["status"] == "draft"
    retried = await alice.post(f"/trips/{trip['id']}/plan", json={})
    assert parse_sse(retried.text)[-1]["kind"] == "done"
    assert (await alice.get(f"/trips/{trip['id']}")).json()["status"] == "planned"


async def test_failure_after_the_agents_restores_status(
    alice: AsyncClient, trip: dict[str, object], monkeypatch: pytest.MonkeyPatch
) -> None:
    from app.services.trips import TripService

    async def broken(*_: object, **__: object) -> None:
        raise RuntimeError("database went away")

    monkeypatch.setattr(TripService, "replace_agent_output", broken)
    events = parse_sse((await alice.post(f"/trips/{trip['id']}/plan", json={})).text)
    assert events[-1]["agent"] == "travya"
    assert events[-1]["kind"] == "error"
    assert "unavailable" in str(events[-1]["message"])
    detail = (await alice.get(f"/trips/{trip['id']}")).json()
    assert detail["status"] == "draft"
    assert detail["plan"] is None
    monkeypatch.undo()
    again = await alice.post(f"/trips/{trip['id']}/plan", json={})
    assert parse_sse(again.text)[-1]["kind"] == "done"


async def test_geocoder_failure_still_saves_the_plan(
    alice: AsyncClient, trip: dict[str, object], monkeypatch: pytest.MonkeyPatch
) -> None:
    from app.integrations.fakes import FakeAutocomplete, FakeGuides

    async def down(*_: object, **__: object) -> list[object]:
        raise RuntimeError("photon is down")

    async def slow_guide(*_: object, **__: object) -> None:
        import asyncio

        await asyncio.sleep(1)

    monkeypatch.setattr(FakeAutocomplete, "suggest", down)
    monkeypatch.setattr("app.services.planning._PlaceResolver._match", lambda *_: None)
    monkeypatch.setattr(FakeGuides, "guide", slow_guide)
    monkeypatch.setattr("app.agents.planning.scouts.SCOUT_BUDGET_S", 0.05)
    events = parse_sse((await alice.post(f"/trips/{trip['id']}/plan", json={})).text)
    assert events[-1]["kind"] == "done"
    guide = next(e for e in events if e["agent"] == "guide_scout" and e["kind"] == "progress")
    assert "continuing without it" in str(guide["message"])
    assert (await alice.get(f"/trips/{trip['id']}")).json()["status"] == "planned"
    items = (await alice.get(f"/trips/{trip['id']}/itinerary")).json()
    assert items
    assert all(i["latitude"] is None for i in items)


@pytest.mark.parametrize("stop_after", ["started", "Placing stops on the map"])
async def test_client_leaving_restores_status(
    app: Any, alice: AsyncClient, trip: dict[str, object], stop_after: str
) -> None:
    from sqlmodel import select

    from app.core.db import SessionFactory
    from app.models import User
    from app.services.planning import PlanningService

    async with SessionFactory() as session:
        user = (await session.exec(select(User).where(User.firebase_uid == "uid-alice"))).one()
        planner = PlanningService(session, user, app.state.integrations, app.state.limiter)
        claim = await planner.start(uuid.UUID(str(trip["id"])))
        stream = planner.stream(claim, None)
        async for event in stream:
            if stop_after in (event.kind, event.message):
                break
        assert (await alice.get(f"/trips/{trip['id']}")).json()["status"] == "planning"
        await stream.aclose()
    detail = (await alice.get(f"/trips/{trip['id']}")).json()
    assert detail["status"] == "draft"
    assert (await alice.get(f"/trips/{trip['id']}/itinerary")).json() == []
