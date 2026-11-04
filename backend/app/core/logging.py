"""Structured logging: JSON in production, readable console output locally.

Every log line carries the request id set by asgi-correlation-id.
"""

import logging
import sys

import structlog
from asgi_correlation_id import correlation_id

from app.core.config import settings


def _add_request_id(_: object, __: str, event_dict: structlog.typing.EventDict) -> structlog.typing.EventDict:
    if request_id := correlation_id.get():
        event_dict["request_id"] = request_id
    return event_dict


def configure_logging() -> None:
    shared: list[structlog.typing.Processor] = [
        structlog.contextvars.merge_contextvars,
        structlog.stdlib.add_log_level,
        structlog.stdlib.add_logger_name,
        _add_request_id,
        structlog.processors.TimeStamper(fmt="iso", utc=True),
        structlog.processors.StackInfoRenderer(),
    ]
    renderer: structlog.typing.Processor = (
        structlog.processors.JSONRenderer() if settings.LOG_JSON else structlog.dev.ConsoleRenderer()
    )
    structlog.configure(
        processors=[*shared, structlog.stdlib.ProcessorFormatter.wrap_for_formatter],
        logger_factory=structlog.stdlib.LoggerFactory(),
        cache_logger_on_first_use=True,
    )
    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(
        structlog.stdlib.ProcessorFormatter(
            foreign_pre_chain=shared,
            processors=[
                structlog.stdlib.ProcessorFormatter.remove_processors_meta,
                structlog.processors.format_exc_info,
                renderer,
            ],
        )
    )
    root = logging.getLogger()
    root.handlers = [handler]
    root.setLevel(settings.LOG_LEVEL)
    for noisy in ("uvicorn.access", "httpx", "google_adk", "google_genai"):
        logging.getLogger(noisy).setLevel(logging.WARNING)


def get_logger(name: str) -> structlog.stdlib.BoundLogger:
    return structlog.stdlib.get_logger(name)
