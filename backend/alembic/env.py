"""Alembic migrations, run with the app's async engine settings."""

import asyncio

from sqlalchemy.engine import Connection
from sqlalchemy.ext.asyncio import create_async_engine
from sqlmodel import SQLModel

import app.models  # noqa: F401  (registers every table on the metadata)
from alembic import context
from app.core.config import settings

target_metadata = SQLModel.metadata


def _configure(connection: Connection | None = None) -> None:
    context.configure(
        connection=connection,
        url=None if connection else settings.DATABASE_URL,
        target_metadata=target_metadata,
        compare_type=True,
        literal_binds=connection is None,
    )


def run_migrations_offline() -> None:
    _configure()
    with context.begin_transaction():
        context.run_migrations()


def _run_sync(connection: Connection) -> None:
    _configure(connection)
    with context.begin_transaction():
        context.run_migrations()


async def run_migrations_online() -> None:
    engine = create_async_engine(settings.DATABASE_URL)
    async with engine.connect() as connection:
        await connection.run_sync(_run_sync)
    await engine.dispose()


if context.is_offline_mode():
    run_migrations_offline()
else:
    asyncio.run(run_migrations_online())
