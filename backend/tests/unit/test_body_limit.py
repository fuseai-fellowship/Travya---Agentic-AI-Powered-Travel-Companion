from collections.abc import AsyncIterator

from fastapi import FastAPI
from httpx import ASGITransport, AsyncClient
from pydantic import BaseModel

from app.core.limits import BodySizeLimit


class Payload(BaseModel):
    text: str


def make_app(calls: list[int]) -> FastAPI:
    app = FastAPI()
    app.add_middleware(BodySizeLimit, limit_for=lambda scope: 1000)

    @app.post("/echo")
    async def echo(payload: Payload) -> dict[str, int]:
        calls.append(len(payload.text))
        return {"length": len(payload.text)}

    return app


async def test_small_bodies_pass() -> None:
    calls: list[int] = []
    async with AsyncClient(transport=ASGITransport(app=make_app(calls)), base_url="http://t") as c:
        response = await c.post("/echo", json={"text": "hi"})
    assert response.json() == {"length": 2}


async def test_declared_large_body_is_refused_unread() -> None:
    calls: list[int] = []
    async with AsyncClient(transport=ASGITransport(app=make_app(calls)), base_url="http://t") as c:
        response = await c.post("/echo", json={"text": "x" * 5000})
    assert response.status_code == 413
    assert response.headers["content-type"] == "application/problem+json"
    assert response.json()["title"] == "Content too large"
    assert calls == []


async def test_streamed_large_body_is_cut_off() -> None:
    calls: list[int] = []

    async def chunks() -> AsyncIterator[bytes]:
        yield b'{"text": "'
        for _ in range(50):
            yield b"x" * 100
        yield b'"}'

    async with AsyncClient(transport=ASGITransport(app=make_app(calls)), base_url="http://t") as c:
        response = await c.post(
            "/echo", content=chunks(), headers={"content-type": "application/json"}
        )
    assert response.status_code == 413
    assert calls == []
