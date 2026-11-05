"""Request body size limits, enforced before the app reads the body."""

import json
from collections.abc import Callable

from starlette.types import ASGIApp, Message, Receive, Scope, Send

MB = 1024 * 1024


class _TooLarge(Exception):
    pass


class BodySizeLimit:
    """Answers 413 when a body is larger than `limit_for(scope)` bytes: at once when the
    Content-Length says so, otherwise as soon as the streamed bytes pass the limit."""

    def __init__(self, app: ASGIApp, *, limit_for: Callable[[Scope], int]) -> None:
        self.app = app
        self.limit_for = limit_for

    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return
        limit = self.limit_for(scope)
        declared = dict(scope["headers"]).get(b"content-length")
        if declared is not None and declared.isdigit() and int(declared) > limit:
            await _reject(scope, send, limit)
            return

        received = 0
        too_large = False
        started = False

        async def limited_receive() -> Message:
            nonlocal received, too_large
            message = await receive()
            if message["type"] == "http.request":
                received += len(message.get("body", b""))
                if received > limit:
                    too_large = True
                    raise _TooLarge
            return message

        async def guarded_send(message: Message) -> None:
            nonlocal started
            if too_large and not started:
                return  # the app's answer to a body it never got; ours follows
            if message["type"] == "http.response.start":
                started = True
            await send(message)

        try:
            await self.app(scope, limited_receive, guarded_send)
        except Exception:
            if not too_large:
                raise
        if too_large and not started:
            await _reject(scope, send, limit)


async def _reject(scope: Scope, send: Send, limit: int) -> None:
    body = json.dumps(
        {
            "type": "about:blank",
            "title": "Content too large",
            "status": 413,
            "detail": f"Requests can be at most {limit // MB or 1} MB.",
            "instance": scope.get("path", ""),
        }
    ).encode()
    await send(
        {
            "type": "http.response.start",
            "status": 413,
            "headers": [
                (b"content-type", b"application/problem+json"),
                (b"content-length", str(len(body)).encode()),
                (b"connection", b"close"),
            ],
        }
    )
    await send({"type": "http.response.body", "body": body})
