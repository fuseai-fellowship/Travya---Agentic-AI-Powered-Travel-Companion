"""Owner scoping: another user's ids always look like 404, for every read and write."""

import pytest
from httpx import AsyncClient

pytestmark = pytest.mark.db


async def test_no_cross_user_access(
    alice: AsyncClient, bob: AsyncClient, trip: dict[str, object]
) -> None:
    trip_id = trip["id"]
    item = (
        await alice.post(
            f"/trips/{trip_id}/itinerary", json={"day": "2027-03-10", "title": "Boudhanath"}
        )
    ).json()
    note = (
        await alice.post(
            "/notes", json={"title": "Visa", "content": "On arrival", "trip_id": trip_id}
        )
    ).json()
    conversation = (await alice.post("/conversations", json={"trip_id": trip_id})).json()
    document = (
        await alice.post(
            "/documents", files={"file": ("ticket.pdf", b"%PDF-1.7 test", "application/pdf")}
        )
    ).json()

    forbidden = [
        ("GET", f"/trips/{trip_id}"),
        ("PATCH", f"/trips/{trip_id}"),
        ("DELETE", f"/trips/{trip_id}"),
        ("GET", f"/trips/{trip_id}/itinerary"),
        ("PATCH", f"/trips/{trip_id}/itinerary/{item['id']}"),
        ("DELETE", f"/trips/{trip_id}/itinerary/{item['id']}"),
        ("GET", f"/trips/{trip_id}/bookings"),
        ("GET", f"/trips/{trip_id}/photos"),
        ("GET", f"/trips/{trip_id}/weather"),
        ("GET", f"/trips/{trip_id}/map"),
        ("POST", f"/trips/{trip_id}/plan"),
        ("PATCH", f"/notes/{note['id']}"),
        ("DELETE", f"/notes/{note['id']}"),
        ("PATCH", f"/conversations/{conversation['id']}"),
        ("GET", f"/conversations/{conversation['id']}/messages"),
        ("POST", f"/conversations/{conversation['id']}/messages"),
        ("DELETE", f"/conversations/{conversation['id']}"),
        ("GET", f"/documents/{document['id']}/download"),
        ("DELETE", f"/documents/{document['id']}"),
    ]
    bodies = {"PATCH": {"title": "pwned"}, "POST": {"content": "hi"}}
    for method, path in forbidden:
        body = {} if path.endswith("/plan") else bodies.get(method)
        response = await bob.request(method, path, json=body)
        assert response.status_code == 404, f"{method} {path} -> {response.status_code}"

    # Bob cannot attach his own content to Alice's trip either.
    assert (await bob.post("/notes", json={"title": "x", "trip_id": trip_id})).status_code == 404
    assert (await bob.post("/conversations", json={"trip_id": trip_id})).status_code == 404
    upload = await bob.post(
        "/documents",
        data={"trip_id": trip_id},
        files={"file": ("a.pdf", b"%PDF-1.7", "application/pdf")},
    )
    assert upload.status_code == 404
    assert (
        await bob.post(
            "/feedback", json={"target_type": "trip_plan", "target_id": trip_id, "rating": 1}
        )
    ).status_code == 404

    # Bob's lists stay empty and Alice's data is untouched.
    assert (await bob.get("/trips")).json()["total"] == 0
    assert (await bob.get("/notes")).json()["total"] == 0
    assert (await bob.get("/documents")).json() == []
    assert (await alice.get(f"/trips/{trip_id}")).json()["title"] == trip["title"]
    assert (await alice.get("/notes")).json()["items"][0]["title"] == "Visa"


async def test_no_cross_user_writes_through_bookings_photos_and_links(
    alice: AsyncClient, bob: AsyncClient, trip: dict[str, object]
) -> None:
    trip_id = trip["id"]
    await alice.post(f"/trips/{trip_id}/plan", json={})
    booking = (await alice.get(f"/trips/{trip_id}/bookings")).json()[0]
    conversation = (await alice.post("/conversations", json={})).json()
    await alice.post(f"/conversations/{conversation['id']}/messages", json={"content": "Hi"})
    message = (await alice.get(f"/conversations/{conversation['id']}/messages")).json()["items"][1]

    for path, body in [
        (f"/trips/{trip_id}/bookings/{booking['id']}/confirm", None),
        (f"/trips/{trip_id}/bookings/{booking['id']}/cancel", None),
        (f"/trips/{trip_id}/photos/refresh", None),
        (f"/trips/{trip_id}/itinerary", {"day": "2027-03-10", "title": "Sneaky"}),
        ("/feedback", {"target_type": "message", "target_id": message["id"], "rating": 1}),
    ]:
        response = await bob.post(path, json=body)
        assert response.status_code == 404, f"POST {path} -> {response.status_code}"

    # Bob cannot link his own notes or conversations to Alice's trip.
    note = (await bob.post("/notes", json={"title": "Mine"})).json()
    chat = (await bob.post("/conversations", json={})).json()
    assert (await bob.patch(f"/notes/{note['id']}", json={"trip_id": trip_id})).status_code == 404
    linked = await bob.patch(f"/conversations/{chat['id']}", json={"trip_id": trip_id})
    assert linked.status_code == 404

    bookings = (await alice.get(f"/trips/{trip_id}/bookings")).json()
    assert next(b for b in bookings if b["id"] == booking["id"])["status"] == "quoted"
    titles = [i["title"] for i in (await alice.get(f"/trips/{trip_id}/itinerary")).json()]
    assert "Sneaky" not in titles
