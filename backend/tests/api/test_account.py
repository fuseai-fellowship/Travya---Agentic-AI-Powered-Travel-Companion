from typing import Any

import pytest
from httpx import AsyncClient

from app.core.security import Principal
from tests.api.test_planning import parse_sse
from tests.conftest import BOB, ClientFactory

GUEST = Principal(uid="uid-guest", email=None, name=None, is_anonymous=True, is_admin=False)

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
    app: Any, alice: AsyncClient, trip: dict[str, object]
) -> None:
    from unittest.mock import AsyncMock, patch

    from app.services.chat import APP_NAME

    await alice.post("/notes", json={"title": "bye"})
    user_id = (await alice.get("/me")).json()["id"]
    conversation = (await alice.post("/conversations", json={})).json()
    adk = app.state.adk_sessions
    # What an online chat turn leaves behind in ADK's own tables.
    await adk.create_session(
        app_name=APP_NAME, user_id=user_id, session_id=conversation["id"], state={"x": 1}
    )
    with patch("app.services.users.delete_firebase_user", AsyncMock()) as firebase_delete:
        assert (await alice.delete("/me")).status_code == 204
    firebase_delete.assert_awaited_once_with("uid-alice")
    assert (await adk.list_sessions(app_name=APP_NAME, user_id=user_id)).sessions == []
    # The next request re-creates an empty profile for the same Firebase user.
    assert (await alice.get("/trips")).json()["total"] == 0
    assert (await alice.get("/notes")).json()["total"] == 0


async def test_storage_quotas(
    alice: AsyncClient, client_for: ClientFactory, monkeypatch: pytest.MonkeyPatch
) -> None:
    from app.core.config import settings

    pdf = {"file": ("big.pdf", b"%PDF-1.7 " + b"0" * 700_000, "application/pdf")}
    monkeypatch.setattr(settings, "STORAGE_QUOTA_MB", 1)
    first = await alice.post("/documents", files=pdf)
    assert first.status_code == 201
    over = await alice.post("/documents", files=pdf)
    assert over.status_code == 413
    assert over.json()["title"] == "Storage quota exceeded"
    assert (await alice.delete(f"/documents/{first.json()['id']}")).status_code == 204
    assert (await alice.post("/documents", files=pdf)).status_code == 201

    monkeypatch.setattr(settings, "STORAGE_QUOTA_MB", 25)
    monkeypatch.setattr(settings, "STORAGE_TOTAL_MB", 1)
    full = await client_for(BOB).post("/documents", files=pdf)
    assert full.status_code == 409
    assert full.json()["title"] == "Storage full"

    monkeypatch.setattr(settings, "STORAGE_TOTAL_MB", 200)
    monkeypatch.setattr(settings, "STORAGE_QUOTA_ANONYMOUS_MB", 0)
    guest = client_for(GUEST)
    small = {"file": ("a.pdf", b"%PDF-1.7 tiny", "application/pdf")}
    assert (await guest.post("/documents", files=small)).status_code == 413
    assert (await client_for(BOB).post("/documents", files=small)).status_code == 201
    assert (await guest.get("/documents")).json() == []


async def test_assistant_db_tools_run_concurrently(
    app: Any, alice: AsyncClient, trip: dict[str, object]
) -> None:
    """ADK runs a turn's function calls with asyncio.gather; each needs its own session."""
    import asyncio
    import uuid

    from app.agents.assistant.agent import build_assistant

    me = (await alice.get("/me")).json()
    llm = build_assistant(uuid.UUID(me["id"]), app.state.integrations, None)
    tools = {tool.__name__: tool for tool in llm.tools}
    results = await asyncio.gather(
        tools["my_trips"](),
        tools["trip_itinerary"](trip_id=str(trip["id"])),
        tools["destination_guide"](destination="Kathmandu", question="food"),
        tools["my_trips"](),
    )
    assert all("error" not in result for result in results), results
    assert results[0]["trips"][0]["id"] == trip["id"]
    assert results[1]["trip"]["destination"] == "Kathmandu, Nepal"


async def test_resending_an_unanswered_message_does_not_duplicate_it(
    alice: AsyncClient, monkeypatch: pytest.MonkeyPatch
) -> None:
    from collections.abc import AsyncGenerator

    from app.agents.events import AgentEvent
    from app.services.chat import ChatService

    async def failing(*_: object) -> AsyncGenerator[AgentEvent]:
        yield AgentEvent(agent="assistant", kind="error", message="The assistant is unavailable")

    conversation = (await alice.post("/conversations", json={})).json()
    url = f"/conversations/{conversation['id']}/messages"
    monkeypatch.setattr(ChatService, "reply", failing)
    assert parse_sse((await alice.post(url, json={"content": "Best momo?"})).text)[-1]["kind"] == (
        "error"
    )
    monkeypatch.undo()
    assert parse_sse((await alice.post(url, json={"content": "Best momo?"})).text)[-1]["kind"] == (
        "done"
    )
    messages = (await alice.get(url)).json()["items"]
    assert [m["role"] for m in messages] == ["user", "assistant"]
    assert messages[1]["meta"] == {"tools": []}
    assert (await alice.post(url, json={"content": "   "})).status_code == 422
