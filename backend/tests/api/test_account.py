import pytest
from httpx import AsyncClient

from tests.api.test_planning import parse_sse

pytestmark = pytest.mark.db


async def test_me_profile_and_usage(alice: AsyncClient) -> None:
    me = (await alice.get("/me")).json()
    assert me["email"] == "alice@example.com"
    assert me["is_admin"] is False
    updated = (await alice.patch("/me", json={"home_city": "Kathmandu", "currency": "NPR"})).json()
    assert updated["home_city"] == "Kathmandu"
    assert updated["currency"] == "NPR"
    assert (await alice.get("/me/usage")).json()["llm_runs_remaining_today"] > 0


async def test_notes_crud(alice: AsyncClient) -> None:
    note = (
        await alice.post(
            "/notes", json={"title": "Packing", "content": "**Adapter**", "color": "blue"}
        )
    ).json()
    await alice.post("/notes", json={"title": "Pinned", "is_pinned": True})
    titles = [n["title"] for n in (await alice.get("/notes")).json()["items"]]
    assert titles == ["Pinned", "Packing"]
    assert (await alice.patch(f"/notes/{note['id']}", json={"color": "green"})).json()[
        "color"
    ] == "green"
    assert (await alice.post("/notes", json={"title": "x", "color": "<script>"})).status_code == 422
    assert (await alice.delete(f"/notes/{note['id']}")).status_code == 204


async def test_chat_offline_reply_and_history(alice: AsyncClient) -> None:
    conversation = (await alice.post("/conversations", json={})).json()
    response = await alice.post(
        f"/conversations/{conversation['id']}/messages", json={"content": "Best momo in Patan?"}
    )
    events = parse_sse(response.text)
    assert events[-1]["kind"] == "done"
    messages = (await alice.get(f"/conversations/{conversation['id']}/messages")).json()["items"]
    assert [m["role"] for m in messages] == ["user", "assistant"]
    listed = (await alice.get("/conversations")).json()["items"][0]
    assert listed["title"] == "Best momo in Patan?"
    feedback = await alice.post(
        "/feedback", json={"target_type": "message", "target_id": messages[1]["id"], "rating": 5}
    )
    assert feedback.status_code == 200


async def test_document_upload_validation_and_download(
    alice: AsyncClient, trip: dict[str, object]
) -> None:
    ok = await alice.post(
        "/documents",
        data={"trip_id": trip["id"]},
        files={"file": ("../e-ticket.pdf", b"%PDF-1.7 hello", "application/pdf")},
    )
    assert ok.status_code == 201
    document = ok.json()
    assert document["filename"] == "e-ticket.pdf"
    assert document["content_type"] == "application/pdf"
    renamed_exe = await alice.post(
        "/documents", files={"file": ("photo.png", b"MZ\x90\x00", "image/png")}
    )
    assert renamed_exe.status_code == 422
    download = await alice.get(f"/documents/{document['id']}/download")
    assert download.content == b"%PDF-1.7 hello"
    assert download.headers["content-disposition"] == 'attachment; filename="e-ticket.pdf"'


async def test_delete_account_removes_everything(
    alice: AsyncClient, trip: dict[str, object]
) -> None:
    from unittest.mock import AsyncMock, patch

    await alice.post("/notes", json={"title": "bye"})
    with patch("app.services.users.delete_firebase_user", AsyncMock()) as firebase_delete:
        assert (await alice.delete("/me")).status_code == 204
    firebase_delete.assert_awaited_once_with("uid-alice")
    # The next request re-creates an empty profile for the same Firebase user.
    assert (await alice.get("/trips")).json()["total"] == 0
    assert (await alice.get("/notes")).json()["total"] == 0
