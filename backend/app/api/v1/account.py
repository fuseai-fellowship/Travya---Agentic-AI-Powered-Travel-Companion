"""The signed-in user's profile, usage, notes, documents and feedback."""

import uuid
from typing import Annotated

from fastapi import APIRouter, Depends, File, Form, Query, Response, UploadFile, status

from app.api.deps import (
    AdkSessionsDep,
    CurrentUser,
    IntegrationsDep,
    LimiterDep,
    PrincipalDep,
    SessionDep,
    rate_limit,
)
from app.core.config import settings
from app.core.ratelimit import CALLS_PER_RUN
from app.integrations.storage import content_disposition
from app.schemas.common import Page
from app.schemas.content import (
    DocumentRead,
    DownloadLink,
    FeedbackCreate,
    FeedbackRead,
    MeRead,
    MeUpdate,
    NoteCreate,
    NoteRead,
    NoteUpdate,
    UsageRead,
)
from app.services.documents import DocumentService
from app.services.feedback import submit_feedback
from app.services.notes import NoteService
from app.services.users import delete_account, update_me

router = APIRouter()


def _me(user: CurrentUser, principal: PrincipalDep) -> MeRead:
    return MeRead.model_validate(user.model_dump() | {"is_admin": principal.is_admin})


@router.get("/me", response_model=MeRead, tags=["account"])
async def read_me(user: CurrentUser, principal: PrincipalDep) -> MeRead:
    return _me(user, principal)


@router.patch("/me", response_model=MeRead, tags=["account"])
async def patch_me(
    data: MeUpdate, user: CurrentUser, principal: PrincipalDep, session: SessionDep
) -> MeRead:
    return _me(await update_me(session, user, data), principal)


@router.delete("/me", status_code=status.HTTP_204_NO_CONTENT, tags=["account"])
async def delete_me(
    user: CurrentUser,
    session: SessionDep,
    integrations: IntegrationsDep,
    adk_sessions: AdkSessionsDep,
) -> None:
    await delete_account(session, user, integrations.storage, adk_sessions)


@router.get("/me/usage", response_model=UsageRead, tags=["account"])
async def usage(_: CurrentUser, limiter: LimiterDep) -> UsageRead:
    remaining = await limiter.remaining_llm_budget()
    return UsageRead(
        llm_runs_remaining_today=remaining // CALLS_PER_RUN,
        llm_calls_remaining_today=remaining,
        llm_calls_per_day=settings.LLM_DAILY_REQUEST_BUDGET,
    )


def note_service(session: SessionDep, user: CurrentUser) -> NoteService:
    return NoteService(session, user)


Notes = Annotated[NoteService, Depends(note_service)]


@router.get("/notes", response_model=Page[NoteRead], tags=["notes"])
async def list_notes(
    notes: Notes,
    trip_id: uuid.UUID | None = None,
    limit: Annotated[int, Query(ge=1, le=100)] = 50,
    offset: Annotated[int, Query(ge=0)] = 0,
) -> Page[NoteRead]:
    rows, total = await notes.page(trip_id=trip_id, limit=limit, offset=offset)
    return Page(
        items=[NoteRead.model_validate(n) for n in rows], total=total, limit=limit, offset=offset
    )


@router.post("/notes", response_model=NoteRead, status_code=status.HTTP_201_CREATED, tags=["notes"])
async def create_note(data: NoteCreate, notes: Notes) -> NoteRead:
    return NoteRead.model_validate(await notes.create(data))


@router.patch("/notes/{note_id}", response_model=NoteRead, tags=["notes"])
async def update_note(note_id: uuid.UUID, data: NoteUpdate, notes: Notes) -> NoteRead:
    return NoteRead.model_validate(await notes.update(note_id, data))


@router.delete("/notes/{note_id}", status_code=status.HTTP_204_NO_CONTENT, tags=["notes"])
async def delete_note(note_id: uuid.UUID, notes: Notes) -> None:
    await notes.delete(note_id)


def document_service(
    session: SessionDep, user: CurrentUser, integrations: IntegrationsDep
) -> DocumentService:
    return DocumentService(session, user, integrations.storage)


Documents = Annotated[DocumentService, Depends(document_service)]


@router.get("/documents", response_model=list[DocumentRead], tags=["documents"])
async def list_documents(
    documents: Documents, trip_id: uuid.UUID | None = None
) -> list[DocumentRead]:
    return [DocumentRead.model_validate(d) for d in await documents.for_trip(trip_id)]


@router.post(
    "/documents",
    response_model=DocumentRead,
    status_code=status.HTTP_201_CREATED,
    tags=["documents"],
    dependencies=[Depends(rate_limit("30/hour", "upload"))],
)
async def upload_document(
    documents: Documents,
    file: Annotated[UploadFile, File(description="PDF, PNG, JPEG or WebP")],
    trip_id: Annotated[uuid.UUID | None, Form()] = None,
) -> DocumentRead:
    data = await file.read()
    return DocumentRead.model_validate(
        await documents.upload(file.filename or "document", data, trip_id)
    )


@router.get(
    "/documents/{document_id}/download",
    tags=["documents"],
    responses={200: {"content": {"application/octet-stream": {}}}},
    response_model=DownloadLink,
)
async def download_document(
    document_id: uuid.UUID, documents: Documents
) -> DownloadLink | Response:
    document = await documents.get(document_id)
    if url := await documents.download_url(document):
        return DownloadLink(url=url, expires_in=600)
    return Response(
        await documents.read(document),
        media_type=document.content_type,
        headers={
            "Content-Disposition": content_disposition(document.filename),
            "Cache-Control": "private, no-store",
            "X-Content-Type-Options": "nosniff",
        },
    )


@router.delete(
    "/documents/{document_id}", status_code=status.HTTP_204_NO_CONTENT, tags=["documents"]
)
async def delete_document(document_id: uuid.UUID, documents: Documents) -> None:
    await documents.delete(document_id)


@router.post("/feedback", response_model=FeedbackRead, tags=["feedback"])
async def give_feedback(
    data: FeedbackCreate, user: CurrentUser, session: SessionDep
) -> FeedbackRead:
    return FeedbackRead.model_validate(await submit_feedback(session, user, data))
