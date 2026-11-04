"""OpenTelemetry for the agents, using ADK's built-in instrumentation.

ADK already emits spans for every agent run, LLM call and tool call. This only installs exporters:
Cloud Trace when ENABLE_CLOUD_TRACE is set, and any OTLP endpoint given through the standard
OTEL_EXPORTER_OTLP_* variables (e.g. a local Jaeger).
"""

import os

from app.core.config import settings
from app.core.logging import get_logger

log = get_logger(__name__)


def configure_tracing() -> None:
    otlp = any(k.startswith("OTEL_EXPORTER_OTLP_") and k.endswith("ENDPOINT") for k in os.environ)
    if not (settings.ENABLE_CLOUD_TRACE or otlp):
        return
    from google.adk.telemetry.google_cloud import get_gcp_exporters
    from google.adk.telemetry.setup import maybe_set_otel_providers

    hooks = [get_gcp_exporters(enable_cloud_tracing=True)] if settings.ENABLE_CLOUD_TRACE else []
    maybe_set_otel_providers(hooks)
    log.info("tracing_enabled", cloud_trace=settings.ENABLE_CLOUD_TRACE, otlp=otlp)
