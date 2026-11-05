"""Domain errors and their mapping to RFC 9457 problem+json responses.

Services raise these; routers never build error responses by hand, and stack traces never reach clients.
"""

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse

from app.core.logging import get_logger

log = get_logger(__name__)


class DomainError(Exception):
    status = 400
    title = "Bad request"

    def __init__(self, detail: str | None = None) -> None:
        super().__init__(detail or self.title)
        self.detail = detail or self.title


class NotFound(DomainError):
    status = 404
    title = "Not found"


class Forbidden(DomainError):
    status = 403
    title = "Forbidden"


class Unauthorized(DomainError):
    status = 401
    title = "Not authenticated"


class Conflict(DomainError):
    status = 409
    title = "Conflict"


class PayloadTooLarge(DomainError):
    status = 413
    title = "Content too large"


class QuotaExceeded(DomainError):
    status = 413
    title = "Storage quota exceeded"


class StorageFull(DomainError):
    status = 409
    title = "Storage full"


class InvalidInput(DomainError):
    status = 422
    title = "Invalid input"


class RateLimited(DomainError):
    status = 429
    title = "Too many requests"

    def __init__(self, detail: str | None = None, retry_after: int | None = None) -> None:
        super().__init__(detail)
        self.retry_after = retry_after


class BudgetExhausted(DomainError):
    status = 503
    title = "Demo limit reached"


class UpstreamUnavailable(DomainError):
    status = 503
    title = "Upstream service unavailable"


def _problem(status: int, title: str, detail: str, request: Request) -> dict[str, object]:
    return {
        "type": "about:blank",
        "title": title,
        "status": status,
        "detail": detail,
        "instance": request.url.path,
    }


def install_error_handlers(app: FastAPI) -> None:
    @app.exception_handler(DomainError)
    async def _domain(request: Request, exc: DomainError) -> JSONResponse:
        headers = {}
        if isinstance(exc, RateLimited) and exc.retry_after:
            headers["Retry-After"] = str(exc.retry_after)
        if isinstance(exc, Unauthorized):
            headers["WWW-Authenticate"] = "Bearer"
        return JSONResponse(
            _problem(exc.status, exc.title, exc.detail, request),
            status_code=exc.status,
            headers=headers,
            media_type="application/problem+json",
        )

    @app.exception_handler(RequestValidationError)
    async def _validation(request: Request, exc: RequestValidationError) -> JSONResponse:
        body = _problem(422, "Invalid input", "Request validation failed", request)
        body["errors"] = [
            {"loc": list(e.get("loc", ())), "msg": e.get("msg", ""), "type": e.get("type", "")}
            for e in exc.errors()
        ]
        return JSONResponse(body, status_code=422, media_type="application/problem+json")

    @app.exception_handler(Exception)
    async def _unhandled(request: Request, exc: Exception) -> JSONResponse:
        log.exception("unhandled_error", path=request.url.path)
        return JSONResponse(
            _problem(500, "Internal server error", "Something went wrong on our side.", request),
            status_code=500,
            media_type="application/problem+json",
        )
