"""Conversations with the travel assistant, streamed token by token."""

import uuid
from collections.abc import AsyncIterator
from contextlib import aclosing
from datetime import UTC, datetime

from google.adk.agents.run_config import RunConfig, StreamingMode  # type: ignore[attr-defined]
from google.adk.runners import Runner
from google.adk.sessions import BaseSessionService
from google.genai import types
from sqlmodel import col
from sqlmodel.ext.asyncio.session import AsyncSession

from app.agents.assistant.agent import build_assistant
from app.agents.deadline import deadline_in, until
from app.agents.events import AgentEvent
from app.core.config import settings
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
        _, count = await messages.page(limit=1)
        await messages.add(
            Message(conversation_id=conversation.id, role=MessageRole.user, content=content)
        )
        changes: dict[str, object] = {"last_message_at": datetime.now(UTC)}
        if count == 0 and conversation.title == "New conversation":
            changes["title"] = content.strip().splitlines()[0][:60]
        await self.conversations.update(conversation, changes)
        await self.session.commit()
        return conversation

    async def reply(self, conversation: Conversation, content: str) -> AsyncIterator[AgentEvent]:
        text = ""
        tools_used: list[str] = []
        if settings.OFFLINE_INTEGRATIONS or not settings.gemini_api_keys():
            text = OFFLINE_REPLY
            yield AgentEvent(agent="assistant", kind="token", message=text)
        else:
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
                            tools_used.append(call.name or "")
                            label = TOOL_LABELS.get(call.name or "", "Using a tool")
                            yield AgentEvent(
                                agent="assistant", kind="progress", message=f"{label}…"
                            )
                        if event.partial and event.content and event.content.parts:
                            chunk = "".join(
                                p.text or "" for p in event.content.parts if not p.thought
                            )
                            if chunk:
                                text += chunk
                                yield AgentEvent(agent="assistant", kind="token", message=chunk)
                        elif (
                            event.is_final_response()
                            and event.content
                            and event.content.parts
                            and not text
                        ):
                            text = "".join(
                                p.text or "" for p in event.content.parts if not p.thought
                            )
                            yield AgentEvent(agent="assistant", kind="token", message=text)
            except TimeoutError:
                log.warning("chat_deadline", conversation_id=str(conversation.id))
                yield AgentEvent(
                    agent="assistant",
                    kind="error",
                    message="The assistant took too long to answer. Please try again.",
                    data={"error": "deadline"},
                )
                return
            except BudgetExhausted as exc:
                yield AgentEvent(
                    agent="assistant",
                    kind="error",
                    message=exc.detail,
                    data={"error": type(exc).__name__},
                )
                return
            except Exception as exc:
                log.exception("chat_failed", conversation_id=str(conversation.id))
                yield AgentEvent(
                    agent="assistant",
                    kind="error",
                    message="The assistant is unavailable right now. Please try again in a moment.",
                    data={"error": type(exc).__name__},
                )
                return
        message = await MessageRepository(self.session, conversation.id).add(
            Message(
                conversation_id=conversation.id,
                role=MessageRole.assistant,
                content=text.strip() or "Sorry, I couldn't produce an answer.",
                meta={"tools": list(dict.fromkeys(t for t in tools_used if t))},
            )
        )
        await self.conversations.update(conversation, {"last_message_at": datetime.now(UTC)})
        await self.session.commit()
        yield AgentEvent(agent="assistant", kind="done", data={"message_id": str(message.id)})


def latest_first() -> object:
    return newest_first(Conversation, "last_message_at")
