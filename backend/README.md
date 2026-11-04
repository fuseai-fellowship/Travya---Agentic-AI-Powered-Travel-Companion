# Travya API

FastAPI service with the Google ADK planning pipeline, the travel assistant and the integrations with
open data services. Python 3.13, managed with [uv](https://docs.astral.sh/uv/).

## Layout

```text
app/
├── main.py           app factory, lifespan, middleware
├── api/              dependencies (auth, rate limits) and the v1 routers
├── agents/           planning pipeline (scouts, prompts, checks, offline planner) and assistant
├── core/             settings, database engine, errors, logging, rate limiter, Firebase auth
├── integrations/     ports, adapters, fakes, shared HTTP client, cache TTLs, registry
├── llm/              Gemini model with fallback, embeddings
├── models/           SQLModel tables
├── repositories/     owner-scoped data access
├── schemas/          request, response and structured-output models
├── scripts/          export_openapi.py
└── services/         use cases
alembic/              migrations
tests/                api (needs Postgres), integrations (HTTP mocked), unit
```

## Commands

Run from this directory. The database, Redis and the Auth emulator come from the Compose stack at the
repository root (`make up`); Postgres is on `localhost:5433`.

```sh
uv sync                                    # install, including dev tools
make -C .. up                              # run the API (hot reload) with the rest of the stack
TEST_DATABASE_URL=postgresql+psycopg://travya:travya@localhost:5433/travya_test uv run pytest
uv run pytest -m "not db"                  # tests that need no database
uv run ruff check . && uv run ruff format --check . && uv run mypy app
make -C .. migrate                         # apply migrations to the Compose database
make -C .. revision m="describe the change"  # autogenerate a migration from the models
uv run python -m app.scripts.export_openapi > ../frontend/openapi.json
```

Settings are documented in [Getting started](../docs/getting-started.md#environment-variables) and
read by `app/core/config.py`.

## Documentation

- [Architecture overview](../docs/architecture/overview.md)
- [Agents](../docs/architecture/agents.md)
- [Data model](../docs/architecture/data-model.md)
- [Integrations](../docs/architecture/integrations.md)
- [API reference](../docs/api.md)
- Published site: <https://fuseai-fellowship.github.io/Travya---Agentic-AI-Powered-Travel-Companion/>
