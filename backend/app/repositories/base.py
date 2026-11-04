"""Data access scoped to an owner.

Every query for user data goes through a repository bound to the current user (or to a trip that was
already loaded through the user's repository), so one user can never read or change another's rows.
Missing and foreign rows both raise NotFound, which avoids leaking whether an id exists.
"""

from __future__ import annotations

import uuid
from collections.abc import Sequence
from typing import Any, ClassVar

from sqlalchemy import func
from sqlalchemy.sql import ColumnElement
from sqlmodel import col, select
from sqlmodel.ext.asyncio.session import AsyncSession

from app.core.errors import NotFound
from app.models.base import Table


class ScopedRepository[T: Table]:
    model: ClassVar[type[Any]]
    scope_column: ClassVar[str]
    not_found: ClassVar[str] = "Not found"

    def __init__(self, session: AsyncSession, scope_id: uuid.UUID) -> None:
        self.session = session
        self.scope_id = scope_id

    def _scope(self) -> ColumnElement[bool]:
        return getattr(self.model, self.scope_column) == self.scope_id  # type: ignore[no-any-return]

    async def get(self, id_: uuid.UUID) -> T:
        stmt = select(self.model).where(self.model.id == id_, self._scope())
        obj = (await self.session.exec(stmt)).first()
        if obj is None:
            raise NotFound(self.not_found)
        return obj  # type: ignore[no-any-return]

    async def list(
        self,
        *where: ColumnElement[bool],
        order_by: Sequence[Any] = (),
        limit: int = 50,
        offset: int = 0,
    ) -> tuple[list[T], int]:
        base = select(self.model).where(self._scope(), *where)
        total = (await self.session.exec(select(func.count()).select_from(base.subquery()))).one()
        rows = await self.session.exec(base.order_by(*order_by).limit(limit).offset(offset))
        return list(rows.all()), int(total)

    async def all(self, *where: ColumnElement[bool], order_by: Sequence[Any] = ()) -> list[T]:
        rows = await self.session.exec(
            select(self.model).where(self._scope(), *where).order_by(*order_by)
        )
        return list(rows.all())

    async def add(self, obj: T) -> T:
        if getattr(obj, self.scope_column) != self.scope_id:
            raise NotFound(self.not_found)
        self.session.add(obj)
        await self.session.flush()
        await self.session.refresh(obj)
        return obj

    async def update(self, obj: T, changes: dict[str, Any]) -> T:
        for key, value in changes.items():
            setattr(obj, key, value)
        self.session.add(obj)
        await self.session.flush()
        await self.session.refresh(obj)
        return obj

    async def delete(self, obj: T) -> None:
        await self.session.delete(obj)
        await self.session.flush()

    async def delete_where(self, *where: ColumnElement[bool]) -> None:
        for obj in await self.all(*where):
            await self.session.delete(obj)
        await self.session.flush()


def newest_first(model: Any, column: str = "created_at") -> Any:
    return col(getattr(model, column)).desc()
