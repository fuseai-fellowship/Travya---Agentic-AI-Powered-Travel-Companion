from __future__ import annotations

import uuid

from sqlmodel import col
from sqlmodel.ext.asyncio.session import AsyncSession

from app.models import Note, User
from app.repositories import NoteRepository, TripRepository
from app.schemas.content import NoteCreate, NoteUpdate


class NoteService:
    def __init__(self, session: AsyncSession, user: User) -> None:
        self.session = session
        self.user = user
        self.notes = NoteRepository(session, user.id)

    async def _check_trip(self, trip_id: uuid.UUID | None) -> None:
        if trip_id is not None:
            await TripRepository(self.session, self.user.id).get(trip_id)

    async def page(
        self, *, trip_id: uuid.UUID | None, limit: int, offset: int
    ) -> tuple[list[Note], int]:
        where = [col(Note.trip_id) == trip_id] if trip_id else []
        return await self.notes.page(
            *where,
            order_by=[col(Note.is_pinned).desc(), col(Note.updated_at).desc()],
            limit=limit,
            offset=offset,
        )

    async def create(self, data: NoteCreate) -> Note:
        await self._check_trip(data.trip_id)
        note = await self.notes.add(Note(user_id=self.user.id, **data.model_dump()))
        await self.session.commit()
        return note

    async def update(self, note_id: uuid.UUID, data: NoteUpdate) -> Note:
        note = await self.notes.get(note_id)
        changes = data.model_dump(exclude_unset=True)
        await self._check_trip(changes.get("trip_id"))
        note = await self.notes.update(note, changes)
        await self.session.commit()
        return note

    async def delete(self, note_id: uuid.UUID) -> None:
        await self.notes.delete(await self.notes.get(note_id))
        await self.session.commit()
