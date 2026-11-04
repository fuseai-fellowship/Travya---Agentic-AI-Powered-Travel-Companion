# Getting started

The whole stack runs in Docker Compose: Postgres with pgvector, Redis, the Firebase Auth emulator,
the migration job, the API with hot reload and the Vite dev server. The default configuration needs
no API keys and no network access to third-party services.

## Requirements

- Docker with Compose v2.24 or newer
- [uv](https://docs.astral.sh/uv/) and Node 24, for running linters and tests on the host
- Optional: [pre-commit](https://pre-commit.com/) and Terraform

## Run the stack

```sh
git clone https://github.com/fuseai-fellowship/Travya---Agentic-AI-Powered-Travel-Companion.git travya
cd travya
cp .env.example .env    # works as is: offline integrations, local emulators
make up                 # build and start everything in the background
make logs s=api         # follow one service (omit s= for all)
make down               # stop; the database volume is kept
```

| URL | Service |
|---|---|
| <http://localhost:5173> | Web app (Vite, hot reload) |
| <http://localhost:8000/api/v1/docs> | API with Swagger UI (uvicorn, hot reload) |
| <http://localhost:9099> | Firebase Auth emulator, project `demo-travya` |
| `localhost:5433` | Postgres: databases `travya` and `travya_test`, user and password `travya` |
| `localhost:6379` | Redis |

!!! note "Postgres listens on host port 5433"
    A native Postgres often owns 5432, so `compose.override.yaml` publishes the container's 5432 on
    `127.0.0.1:5433`. Every default URL in `.env.example`, the `Makefile` and the test setup uses 5433.

All ports are bound to `127.0.0.1`. Inside the Compose network the API reaches the other services by
name (`db:5432`, `redis:6379`, `auth:9099`); `compose.yaml` sets those addresses itself and loads the
rest of the configuration from `.env`.

## Offline mode and real agents

`OFFLINE_INTEGRATIONS=true` (the default in `.env.example` and in Compose) swaps every external
adapter for a deterministic fake from `backend/app/integrations/fakes.py`:

- geocoding, places, routing, weather, guides and photos return stable, plausible data (a few real
  cities resolve to their true coordinates, anything else gets hash-based ones);
- the planning pipeline replaces the Gemini planner with `ScriptedPlanner`, which builds an itinerary
  from the scouts' findings, so research, persistence, the map and bookings all work end to end;
- guide embeddings are deterministic hash vectors;
- the assistant answers with a fixed "offline demo mode" message;
- trip documents are kept in memory and disappear when the API restarts.

To run the real agents, edit `.env`:

```sh
GEMINI_API_KEY=<key from Google AI Studio>   # https://aistudio.google.com/apikey
OFFLINE_INTEGRATIONS=false
```

then `make up` again. With `OFFLINE_INTEGRATIONS=false` the API calls OpenStreetMap services,
Open-Meteo, Wikivoyage and Wikimedia Commons directly (Unsplash and OpenRouteService only when their
keys are set). Without a Gemini key the API still uses real data but keeps the scripted planner and the
offline assistant reply.

!!! warning "Free-tier quota"
    A planning run costs one planner call, up to two critic calls and up to two reviser calls, plus
    embedding requests for the guide. The global `LLM_DAILY_REQUEST_BUDGET` counts runs, not model
    calls, and protects the key's daily quota.

## Firebase Auth emulator

Locally nobody needs a Firebase project. The `auth` service runs the Firebase Auth emulator for the
demo project `demo-travya`; the web app signs in against it (email/password and the anonymous
"Try the demo" path), and the API verifies the emulator's tokens because `FIREBASE_AUTH_EMULATOR_HOST`
is set. Emulator accounts live in memory and are lost when the container restarts; the matching
`users` rows in Postgres stay and are reused if the same uid signs in again.

To call the API from a terminal, create an anonymous emulator user and keep its ID token:

```sh
TOKEN=$(curl -s -X POST \
  'http://localhost:9099/identitytoolkit.googleapis.com/v1/accounts:signUp?key=demo-api-key' \
  -H 'Content-Type: application/json' -d '{"returnSecureToken":true}' | jq -r .idToken)
curl -s http://localhost:8000/api/v1/me -H "Authorization: Bearer $TOKEN"
```

Never set `FIREBASE_AUTH_EMULATOR_HOST` outside local development: it disables signature checks.

## Make targets

| Target | What it does |
|---|---|
| `make help` | List the targets |
| `make up` | Build and start the dev stack in the background (hot reload) |
| `make down` | Stop the stack; the database volume is kept |
| `make logs [s=<service>]` | Follow logs for all services or one |
| `make migrate` | Apply Alembic migrations to the Compose database |
| `make revision m="<message>"` | Autogenerate a migration from the models |
| `make test` | Backend pytest (needs `make up` for Postgres) and frontend Vitest |
| `make lint` | Ruff, Ruff format check, mypy, Biome and `tsc` |
| `make fmt` | Auto-fix lint findings and format both apps |
| `make openapi` | Export the OpenAPI document to `frontend/openapi.json` |
| `make client` | Export the OpenAPI document and regenerate the typed frontend client |
| `make e2e` | Playwright against the production images in a separate Compose project |
| `make tf-init bucket=<state-bucket>` | Initialise Terraform with the GCS state bucket |
| `make tf-plan` / `make tf-apply` | Plan into `infra/terraform/tfplan`, then apply it |

## Running tests

```sh
(cd backend && uv sync) && (cd frontend && npm ci)
make up       # the API tests need the Compose Postgres (database travya_test)
make test     # pytest and Vitest
make lint
make e2e      # optional: Playwright on the production images, offline integrations
```

The backend suite forces offline integrations and drops `GEMINI_API_KEY` and `REDIS_URL`
(`backend/tests/conftest.py`), so it never calls a real service. It recreates the schema in
`travya_test` from the models and truncates every table after each test.

| Command (from `backend/`) | Runs |
|---|---|
| `uv run pytest -m "not db"` | Unit and adapter tests; no database needed |
| `TEST_DATABASE_URL=... uv run pytest` | Everything, including the API tests marked `db` |
| `RUN_LIVE=1 uv run pytest -m live tests/integrations` | Smoke tests against the real services |

Adapter tests mock HTTP with `respx`; the live smoke tests are opt-in and skipped otherwise.

## Environment variables

Settings are read once by `backend/app/core/config.py` (pydantic-settings). Empty values are ignored,
so the default applies. Defaults below are the code defaults; `.env.example` overrides a few of them for
local development, as noted.

### Runtime

| Variable | Default | Notes |
|---|---|---|
| `ENVIRONMENT` | `local` | `local`, `test`, `staging` or `production`. Staging and production refuse to start without `GEMINI_API_KEY`, `REDIS_URL`, a non-localhost `DATABASE_URL` and, with GCS storage, `GCS_BUCKET`; they also add HSTS. |
| `PROJECT_NAME` | `Travya` | API title |
| `API_V1_PREFIX` | `/api/v1` | Route prefix |
| `FRONTEND_ORIGINS` | `["http://localhost:5173"]` | JSON list of browser origins allowed by CORS |
| `LOG_LEVEL` | `INFO` | Root log level |
| `LOG_JSON` | `false` | JSON logs (production) instead of console output |
| `SENTRY_DSN` | unset | Optional error reporting, sent without PII |

### Data

| Variable | Default | Notes |
|---|---|---|
| `DATABASE_URL` | `postgresql+psycopg://travya:travya@localhost:5433/travya` | Postgres 17 with pgvector. Neon needs `?sslmode=require`. |
| `DB_POOL_SIZE` | `5` | Connection pool size; `max_overflow` is the same number |
| `REDIS_URL` | unset | Rate limits and the HTTP cache; in memory when unset. `.env.example`: `redis://localhost:6379/0`. Upstash: `rediss://...` |
| `TEST_DATABASE_URL` | `...@localhost:5433/travya_test` | pytest only |

### Authentication

| Variable | Default | Notes |
|---|---|---|
| `FIREBASE_PROJECT_ID` | `demo-travya` | Project whose ID tokens are accepted |
| `FIREBASE_AUTH_EMULATOR_HOST` | unset | Read by firebase-admin, not by `Settings`. `.env.example`: `localhost:9099`. Local only. |

### Model

| Variable | Default | Notes |
|---|---|---|
| `GEMINI_API_KEY` | unset | Google AI Studio key. Without it the scripted planner and the offline assistant are used. |
| `GEMINI_MODEL` | `gemini-flash-latest` | Model for every agent |
| `GEMINI_FALLBACK_MODEL` | `gemini-flash-lite-latest` | Used when the primary model answers 429 or 5xx |
| `GEMINI_EMBEDDING_MODEL` | `gemini-embedding-2` | Guide embeddings |
| `EMBEDDING_DIM` | `768` | Must match the `vector(768)` column in `knowledge_chunks` |
| `LLM_DAILY_REQUEST_BUDGET` | `400` | Global cap on agent runs (plans and chat messages) per day |

### Abuse controls

Per user, in [`limits`](https://limits.readthedocs.io/) notation (`<count>/<second|minute|hour|day>`).

| Variable | Default | Applies to |
|---|---|---|
| `RATE_LIMIT_DEFAULT` | `120/minute` | Every authenticated request |
| `RATE_LIMIT_PLAN` | `6/hour` | `POST /trips/{trip_id}/plan` |
| `RATE_LIMIT_CHAT` | `40/hour` | `POST /conversations/{conversation_id}/messages` |

### External services

| Variable | Default | Notes |
|---|---|---|
| `OFFLINE_INTEGRATIONS` | `false` | `true` swaps every adapter for its fake. `.env.example` and Compose: `true`. |
| `HTTP_USER_AGENT` | `Travya/1.0 (+<repository URL>)` | OpenStreetMap services require an identifying agent with a contact |
| `HTTP_TIMEOUT_SECONDS` | `15` | Default outbound timeout |
| `UNSPLASH_ACCESS_KEY` | unset | Enables Unsplash photos; Wikimedia Commons otherwise |
| `ORS_API_KEY` | unset | Enables OpenRouteService routing; FOSSGIS OSRM otherwise |

### Document storage

| Variable | Default | Notes |
|---|---|---|
| `STORAGE_BACKEND` | `local` | `local` or `gcs` |
| `LOCAL_STORAGE_DIR` | `./.storage` | Local file root |
| `GCS_BUCKET` | unset | Required with `gcs` |
| `MAX_UPLOAD_MB` | `10` | Upload size limit |

### Frontend build variables

Vite inlines these into the public bundle at build time, so they must never hold secrets. The Firebase
web API key is a public project identifier.

| Variable | Local value |
|---|---|
| `VITE_API_URL` | `http://localhost:8000` |
| `VITE_FIREBASE_API_KEY` | `demo-api-key` |
| `VITE_FIREBASE_AUTH_DOMAIN` | `demo-travya.firebaseapp.com` |
| `VITE_FIREBASE_PROJECT_ID` | `demo-travya` |
| `VITE_FIREBASE_AUTH_EMULATOR_URL` | `http://localhost:9099` (leave empty for production builds) |
