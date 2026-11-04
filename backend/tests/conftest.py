"""Test setup: offline integrations, a real Postgres (pgvector) database, and fake Firebase principals."""

import os

os.environ.setdefault("ENVIRONMENT", "test")
os.environ["OFFLINE_INTEGRATIONS"] = "true"
os.environ.pop("GEMINI_API_KEY", None)
os.environ.pop("REDIS_URL", None)
os.environ["DATABASE_URL"] = os.environ.get(
    "TEST_DATABASE_URL", "postgresql+psycopg://travya:travya@localhost:5432/travya_test"
)
os.environ["LOCAL_STORAGE_DIR"] = os.environ.get("TEST_STORAGE_DIR", "/tmp/travya-test-storage")

from collections.abc import AsyncIterator, Callable

import pytest
from asgi_lifespan import LifespanManager
from httpx import ASGITransport, AsyncClient
from sqlalchemy import text
from sqlmodel import SQLModel

import app.models
from app.core.db import engine
from app.core.security import Principal

ALICE = Principal(
    uid="uid-alice", email="alice@example.com", name="Alice", is_anonymous=False, is_admin=False
)
BOB = Principal(
    uid="uid-bob", email="bob@example.com", name="Bob", is_anonymous=False, is_admin=False
)


@pytest.fixture(scope="session")
async def database() -> AsyncIterator[None]:
    async with engine.begin() as connection:
        await connection.execute(text("CREATE EXTENSION IF NOT EXISTS vector"))
        await connection.run_sync(SQLModel.metadata.drop_all)
        await connection.run_sync(SQLModel.metadata.create_all)
    yield
    await engine.dispose()


@pytest.fixture
async def clean_db(database: None) -> AsyncIterator[None]:
    yield
    tables = ", ".join(f'"{t.name}"' for t in reversed(SQLModel.metadata.sorted_tables))
    async with engine.begin() as connection:
        await connection.execute(text(f"TRUNCATE {tables} CASCADE"))


@pytest.fixture
async def app(clean_db: None) -> AsyncIterator[object]:
    from app.main import create_app

    application = create_app()
    async with LifespanManager(application):
        yield application


ClientFactory = Callable[[Principal | None], AsyncClient]


@pytest.fixture
async def client_for(app: object) -> AsyncIterator[ClientFactory]:
    """Returns a client authenticated as the given principal (None = anonymous request)."""
    from app.api.deps import get_principal

    clients: list[AsyncClient] = []

    def make(principal: Principal | None) -> AsyncClient:
        async def override() -> Principal:
            assert principal is not None
            return principal

        class _Client(AsyncClient):
            async def request(self, *args: object, **kwargs: object):  # type: ignore[no-untyped-def,override]
                if principal is None:
                    app.dependency_overrides.pop(get_principal, None)  # type: ignore[attr-defined]
                else:
                    app.dependency_overrides[get_principal] = override  # type: ignore[attr-defined]
                return await super().request(*args, **kwargs)  # type: ignore[arg-type]

        client = _Client(transport=ASGITransport(app=app), base_url="http://test/api/v1")  # type: ignore[arg-type]
        clients.append(client)
        return client

    yield make
    for client in clients:
        await client.aclose()


@pytest.fixture
async def alice(client_for: ClientFactory) -> AsyncClient:
    return client_for(ALICE)


@pytest.fixture
async def bob(client_for: ClientFactory) -> AsyncClient:
    return client_for(BOB)


@pytest.fixture
async def anonymous(client_for: ClientFactory) -> AsyncClient:
    return client_for(None)


TRIP = {
    "title": "Kathmandu valley",
    "destination": "Kathmandu, Nepal",
    "origin": "Paris",
    "start_date": "2027-03-10",
    "end_date": "2027-03-12",
    "travelers": 2,
    "budget": "1500.00",
    "currency": "USD",
    "pace": "balanced",
    "interests": ["culture", "food"],
}


@pytest.fixture
async def trip(alice: AsyncClient) -> dict[str, object]:
    response = await alice.post("/trips", json=TRIP)
    assert response.status_code == 201, response.text
    return response.json()  # type: ignore[no-any-return]
