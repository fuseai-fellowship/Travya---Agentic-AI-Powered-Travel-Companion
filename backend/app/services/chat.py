"""Conversations with the travel assistant, streamed token by token."""

import uuid
from collections.abc import AsyncGenerator
from contextlib import aclosing
from dataclasses import dataclass, field
from datetime import UTC, datetime

import anyio
from google.adk.agents.run_config import RunConfig, StreamingMode  # type: ignore[attr-defined]
from google.adk.runners import Runner
from google.adk.sessions import BaseSessionService
from google.genai import types
from sqlmodel import col, update
from sqlmodel.ext.asyncio.session import AsyncSession

from app.agents.assistant.agent import build_assistant
from app.agents.deadline import deadline_in, until
from app.agents.events import AgentEvent
from app.core.config import settings
from app.core.db import SessionFactory
from app.core.errors import BudgetExhausted
from app.core.logging import get_logger
from app.core.ratelimit import Limiter
from app.integrations.registry import Integrations
from app.models import Conversation, Message, MessageRole, User
from app.repositories import ConversationRepository, MessageRepository, TripRepository, newest_first
from app.schemas.content import ConversationCreate, ConversationUpdate

log = get_logger(__name__)

APP_NAME = "travya-assistant"
TOOL_LABELS = {
    "search_places": "Searching OpenStreetMap",
    "weather_forecast": "Checking the weather",
    "destination_guide": "Reading the travel guide",
    "my_trips": "Looking at your trips",
    "trip_itinerary": "Opening your itinerary",
}
OFFLINE_REPLY = (
    "I'm running in offline demo mode, so I can't call the AI model right now. "
    "You can still plan trips, explore the map and manage bookings."
)


class ChatService:
    def __init__(
        self,
        session: AsyncSession,
        user: User,
        integrations: Integrations,
        limiter: Limiter,
        sessions: BaseSessionService,
    ) -> None:
        self.session = session
        self.user = user
        self.integrations = integrations
        self.limiter = limiter
        self.adk_sessions = sessions
        self.conversations = ConversationRepository(session, user.id)

    async def page(
        self, *, archived: bool, limit: int, offset: int
    ) -> tuple[list[Conversation], int]:
        return await self.conversations.page(
            col(Conversation.is_archived) == archived,
            order_by=[
                col(Conversation.is_favorite).desc(),
                col(Conversation.last_message_at).desc(),
            ],
            limit=limit,
            offset=offset,
        )

    async def create(self, data: ConversationCreate) -> Conversation:
        if data.trip_id:
            await TripRepository(self.session, self.user.id).get(data.trip_id)
        conversation = await self.conversations.add(
            Conversation(
                user_id=self.user.id, trip_id=data.trip_id, title=data.title or "New conversation"
            )
        )
        await self.session.commit()
        return conversation

    async def update(self, conversation_id: uuid.UUID, data: ConversationUpdate) -> Conversation:
        conversation = await self.conversations.get(conversation_id)
        changes = data.model_dump(exclude_unset=True)
        if changes.get("trip_id"):
            await TripRepository(self.session, self.user.id).get(changes["trip_id"])
        conversation = await self.conversations.update(conversation, changes)
        await self.session.commit()
        return conversation

    async def delete(self, conversation_id: uuid.UUID) -> None:
        conversation = await self.conversations.get(conversation_id)
        await self.conversations.delete(conversation)
        await self.session.commit()
        await self.adk_sessions.delete_session(
            app_name=APP_NAME, user_id=str(self.user.id), session_id=str(conversation_id)
        )

    async def messages(
        self, conversation_id: uuid.UUID, *, limit: int, offset: int
    ) -> tuple[list[Message], int]:
        conversation = await self.conversations.get(conversation_id)
        return await MessageRepository(self.session, conversation.id).page(
            order_by=[col(Message.created_at)], limit=limit, offset=offset
        )

    async def start(self, conversation_id: uuid.UUID, content: str) -> Conversation:
        conversation = await self.conversations.get(conversation_id)
        await self.limiter.check_llm_budget()
        messages = MessageRepository(self.session, conversation.id)
        last, count = await messages.page(order_by=[col(Message.created_at).desc()], limit=1)
        # "Send again" after a dropped connection must not store the same question twice.
        if not (last and last[0].role == MessageRole.user and last[0].content == content):
            await messages.add(
                Message(conversation_id=conversation.id, role=MessageRole.user, content=content)
            )
        changes: dict[str, object] = {"last_message_at": datetime.now(UTC)}
        if count == 0 and conversation.title == "New conversation":
            changes["title"] = content.splitlines()[0][:60]
        await self.conversations.update(conversation, changes)
        await self.session.commit()
        return conversation

    async def reply(self, conversation: Conversation, content: str) -> AsyncGenerator[AgentEvent]:
        """Streams the answer and saves it. Whatever ends the turn early (an error, the deadline,
        the client going away), the text produced so far is saved and marked interrupted."""
        turn = _Turn()
        message_id: uuid.UUID | None = None
        try:
            async with aclosing(self._answer(conversation, content, turn)) as events:
                async for event in events:
                    yield event
        finally:
            if turn.complete or turn.text.strip():
                with anyio.CancelScope(shield=True):
                    message_id = await self._save(conversation, turn)
        if turn.complete:
            if message_id is None:
                yield AgentEvent(
                    agent="assistant",
                    kind="error",
                    message="The answer could not be saved. Please try again.",
                    data={"error": "not_saved"},
                )
            else:
                yield AgentEvent(
                    agent="assistant", kind="done", data={"message_id": str(message_id)}
                )

    async def _save(self, conversation: Conversation, turn: "_Turn") -> uuid.UUID | None:
        """Own short session: the request's may be mid-transaction or already closed."""
        meta: dict[str, object] = {"tools": list(dict.fromkeys(t for t in turn.tools if t))}
        if not turn.complete:
            meta["interrupted"] = True
        try:
            async with SessionFactory() as session:
                message = Message(
                    conversation_id=conversation.id,
                    role=MessageRole.assistant,
                    content=turn.text.strip() or "Sorry, I couldn't produce an answer.",
                    meta=meta,
                )
                session.add(message)
                await session.exec(
                    update(Conversation)
                    .where(col(Conversation.id) == conversation.id)
                    .values(last_message_at=datetime.now(UTC))
                )
                await session.commit()
                return message.id
        except Exception:
            log.exception("chat_reply_not_saved", conversation_id=str(conversation.id))
            return None

    async def _answer(
        self, conversation: Conversation, content: str, turn: "_Turn"
    ) -> AsyncGenerator[AgentEvent]:
        if settings.OFFLINE_INTEGRATIONS or not settings.gemini_api_keys():
            turn.text = OFFLINE_REPLY
            yield AgentEvent(agent="assistant", kind="token", message=turn.text)
            turn.complete = True
            return
        agent = build_assistant(
            self.user.id,
            self.integrations,
            conversation.trip_id,
            budget=self.limiter.spend_llm_budget,
        )
        runner = Runner(app_name=APP_NAME, agent=agent, session_service=self.adk_sessions)
        user_id, session_id = str(self.user.id), str(conversation.id)
        if not await self.adk_sessions.get_session(
            app_name=APP_NAME, user_id=user_id, session_id=session_id
        ):
            await self.adk_sessions.create_session(
                app_name=APP_NAME, user_id=user_id, session_id=session_id
            )
        deadline = deadline_in(settings.CHAT_DEADLINE_SECONDS)
        try:
            async with aclosing(
                runner.run_async(
                    user_id=user_id,
                    session_id=session_id,
                    new_message=types.Content(role="user", parts=[types.Part(text=content)]),
                    run_config=RunConfig(streaming_mode=StreamingMode.SSE, max_llm_calls=8),
                )
            ) as events:
                async for event in until(events, deadline):
                    for call in event.get_function_calls():
                        turn.tools.append(call.name or "")
                        label = TOOL_LABELS.get(call.name or "", "Using a tool")
                        yield AgentEvent(agent="assistant", kind="progress", message=f"{label}…")
                    if event.partial and event.content and event.content.parts:
                        chunk = "".join(p.text or "" for p in event.content.parts if not p.thought)
                        if chunk:
                            turn.text += chunk
                            yield AgentEvent(agent="assistant", kind="token", message=chunk)
                    elif (
                        event.is_final_response()
                        and event.content
                        and event.content.parts
                        and not turn.text
                    ):
                        turn.text = "".join(
                            p.text or "" for p in event.content.parts if not p.thought
                        )
                        yield AgentEvent(agent="assistant", kind="token", message=turn.text)
            turn.complete = True
        except TimeoutError:
            log.warning("chat_deadline", conversation_id=str(conversation.id))
            yield _error("The assistant took too long to answer. Please try again.", "deadline")
        except BudgetExhausted as exc:
            yield _error(exc.detail, type(exc).__name__)
        except Exception as exc:
            log.exception("chat_failed", conversation_id=str(conversation.id))
            yield _error(
                "The assistant is unavailable right now. Please try again in a moment.",
                type(exc).__name__,
            )


@dataclass
class _Turn:
    text: str = ""
    tools: list[str] = field(default_factory=list)
    complete: bool = False


def _error(message: str, code: str) -> AgentEvent:
    return AgentEvent(agent="assistant", kind="error", message=message, data={"error": code})


def latest_first() -> object:
    return newest_first(Conversation, "last_message_at")
