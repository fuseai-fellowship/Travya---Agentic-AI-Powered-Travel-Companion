import uuid
from collections.abc import AsyncIterator
from typing import Annotated

from fastapi import APIRouter, Depends, Query, status
from sse_starlette import EventSourceResponse, ServerSentEvent

from app.api.deps import (
    AdkSessionsDep,
    CurrentUser,
    IntegrationsDep,
    LimiterDep,
    SessionDep,
    rate_limit,
)
from app.core.config import settings
from app.schemas.common import Page
from app.schemas.content import (
    ChatRequest,
    ConversationCreate,
    ConversationRead,
    ConversationUpdate,
    MessageRead,
)
from app.services.chat import ChatService

router = APIRouter(prefix="/conversations", tags=["chat"])


def get_service(
    session: SessionDep,
    user: CurrentUser,
    integrations: IntegrationsDep,
    limiter: LimiterDep,
    adk_sessions: AdkSessionsDep,
) -> ChatService:
    return ChatService(session, user, integrations, limiter, adk_sessions)


Service = Annotated[ChatService, Depends(get_service)]


@router.get("", response_model=Page[ConversationRead])
async def list_conversations(
    service: Service,
    archived: bool = False,
    limit: Annotated[int, Query(ge=1, le=100)] = 30,
    offset: Annotated[int, Query(ge=0)] = 0,
) -> Page[ConversationRead]:
    rows, total = await service.page(archived=archived, limit=limit, offset=offset)
    return Page(
        items=[ConversationRead.model_validate(c) for c in rows],
        total=total,
        limit=limit,
        offset=offset,
    )


@router.post("", response_model=ConversationRead, status_code=status.HTTP_201_CREATED)
async def create_conversation(data: ConversationCreate, service: Service) -> ConversationRead:
    return ConversationRead.model_validate(await service.create(data))


@router.patch("/{conversation_id}", response_model=ConversationRead)
async def update_conversation(
    conversation_id: uuid.UUID, data: ConversationUpdate, service: Service
) -> ConversationRead:
    return ConversationRead.model_validate(await service.update(conversation_id, data))


@router.delete("/{conversation_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_conversation(conversation_id: uuid.UUID, service: Service) -> None:
    await service.delete(conversation_id)


@router.get("/{conversation_id}/messages", response_model=Page[MessageRead])
async def list_messages(
    conversation_id: uuid.UUID,
    service: Service,
    limit: Annotated[int, Query(ge=1, le=200)] = 100,
    offset: Annotated[int, Query(ge=0)] = 0,
) -> Page[MessageRead]:
    rows, total = await service.messages(conversation_id, limit=limit, offset=offset)
    return Page(
        items=[MessageRead.model_validate(m) for m in rows], total=total, limit=limit, offset=offset
    )


@router.post(
    "/{conversation_id}/messages",
    summary="Send a message and stream the assistant's reply (Server-Sent Events)",
    response_class=EventSourceResponse,
    dependencies=[Depends(rate_limit(settings.RATE_LIMIT_CHAT, "chat"))],
    responses={
        200: {"content": {"text/event-stream": {}}, "description": "Stream of AgentEvent objects"}
    },
)
async def send_message(
    conversation_id: uuid.UUID, data: ChatRequest, service: Service
) -> EventSourceResponse:
    conversation = await service.start(conversation_id, data.content)

    async def events() -> AsyncIterator[ServerSentEvent]:
        async for event in service.reply(conversation, data.content):
            yield ServerSentEvent(data=event.model_dump_json(), event=event.kind)

    return EventSourceResponse(events(), ping=15, headers={"X-Accel-Buffering": "no"})
