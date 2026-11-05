#!/bin/sh
# Container entry point. Hosts without a separate migration job (e.g. Hugging Face Spaces) set
# RUN_MIGRATIONS_ON_START=true; Cloud Run runs migrations as its own job before a deploy.
set -e
if [ "${RUN_MIGRATIONS_ON_START:-false}" = "true" ]; then
  alembic upgrade head
fi
exec uvicorn app.main:app --host 0.0.0.0 --port "${PORT:-8000}" \
  --proxy-headers --forwarded-allow-ips='*' --no-server-header
