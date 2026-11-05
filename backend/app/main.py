"""Travya API application factory."""

from collections.abc import AsyncIterator, Awaitable, Callable
from contextlib import asynccontextmanager

import sentry_sdk
from asgi_correlation_id import CorrelationIdMiddleware
from cashews import cache
from fastapi import FastAPI, Request, Response
from fastapi.middleware.cors import CORSMiddleware
from fastapi.routing import APIRoute
from google.adk.sessions import DatabaseSessionService
from sentry_sdk.scrubber import DEFAULT_DENYLIST, EventScrubber
from sqlalchemy import text
from starlette.types import Scope

from app.api.v1 import router as v1_router
from app.core.config import settings
from app.core.db import engine
from app.core.errors import install_error_handlers
from app.core.limits import MB, BodySizeLimit
from app.core.logging import configure_logging, get_logger
from app.core.ratelimit import Limiter
from app.core.security import init_firebase
from app.core.telemetry import configure_tracing
from app.integrations.http import create_http_client
from app.integrations.registry import build_integrations

log = get_logger(__name__)

SECURITY_HEADERS = {
    "X-Content-Type-Options": "nosniff",
    "X-Frame-Options": "DENY",
    "Referrer-Policy": "strict-origin-when-cross-origin",
    "Content-Security-Policy": "default-src 'none'; frame-ancestors 'none'",
    "Permissions-Policy": "camera=(), microphone=(), geolocation=()",
}
DOCS_PATHS = ("/api/v1/docs", "/api/v1/redoc")
SENTRY_DENYLIST = ["key", "keys", "api_key", "api_keys", "token", "id_token", "credentials"]


async def _adk_session_service() -> DatabaseSessionService:
    """ADK keeps its session tables in their own `adk` schema, apart from the app's tables."""
    async with engine.begin() as connection:
        await connection.execute(text("CREATE SCHEMA IF NOT EXISTS adk"))
    adk_engine = engine.execution_options(schema_translate_map={None: "adk"})
    return DatabaseSessionService(db_engine=adk_engine)


def init_sentry() -> None:
    """Errors only, without the data around them: frame locals can hold a Gemini key (`key`)
    and request bodies hold users' trips and chats."""
    if not settings.SENTRY_DSN:
        return
    sentry_sdk.init(
        dsn=settings.SENTRY_DSN,
        environment=settings.ENVIRONMENT,
        traces_sample_rate=0.1,
        send_default_pii=False,
        include_local_variables=False,
        max_request_body_size="never",
        event_scrubber=EventScrubber(
            denylist=[*DEFAULT_DENYLIST, *SENTRY_DENYLIST], recursive=True
        ),
    )


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    configure_logging()
    init_sentry()
    configure_tracing()
    init_firebase()
    cache.setup(settings.REDIS_URL or "mem://")
    http = create_http_client(settings)
    app.state.integrations = build_integrations(settings, http)
    app.state.limiter = Limiter()
    app.state.adk_sessions = await _adk_session_service()
    log.info("startup", environment=settings.ENVIRONMENT, offline=settings.OFFLINE_INTEGRATIONS)
    yield
    await http.aclose()
    await cache.close()
    await engine.dispose()


def _request_id_ok(value: str) -> bool:
    """Accept proxy-issued IDs (e.g. Hugging Face's) as long as they are safe to log."""
    return 8 <= len(value) <= 128 and all(c.isalnum() or c in "-_.:=" for c in value)


def _body_limit(scope: Scope) -> int:
    """Uploads may carry a whole document; everything else is small JSON."""
    if scope["method"] == "POST" and scope["path"] == f"{settings.API_V1_PREFIX}/documents":
        return (settings.MAX_UPLOAD_MB + 1) * MB  # multipart framing and the form fields
    return MB


def _operation_id(route: APIRoute) -> str:
    return f"{route.tags[0]}-{route.name}" if route.tags else route.name


def create_app() -> FastAPI:
    app = FastAPI(
        title=f"{settings.PROJECT_NAME} API",
        version="1.0.0",
        summary="Multi-agent travel planning on Google ADK, Gemini and open map data",
        openapi_url=f"{settings.API_V1_PREFIX}/openapi.json",
        docs_url=DOCS_PATHS[0],
        redoc_url=DOCS_PATHS[1],
        generate_unique_id_function=_operation_id,
        lifespan=lifespan,
    )
    install_error_handlers(app, cors_origins=settings.FRONTEND_ORIGINS)
    app.add_middleware(BodySizeLimit, limit_for=_body_limit)

    @app.middleware("http")
    async def security_headers(
        request: Request, call_next: Callable[[Request], Awaitable[Response]]
    ) -> Response:
        response = await call_next(request)
        for name, value in SECURITY_HEADERS.items():
            if name == "Content-Security-Policy" and request.url.path in DOCS_PATHS:
                continue  # Swagger UI needs its own scripts
            response.headers.setdefault(name, value)
        if settings.is_production:
            response.headers.setdefault(
                "Strict-Transport-Security", "max-age=63072000; includeSubDomains"
            )
        return response

    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.FRONTEND_ORIGINS,
        allow_methods=["GET", "POST", "PATCH", "DELETE"],
        allow_headers=["Authorization", "Content-Type", "X-Request-ID"],
        expose_headers=["X-Request-ID", "Retry-After"],
        max_age=600,
    )
    app.add_middleware(CorrelationIdMiddleware, validator=_request_id_ok)
    app.include_router(v1_router, prefix=settings.API_V1_PREFIX)
    return app


app = create_app()
