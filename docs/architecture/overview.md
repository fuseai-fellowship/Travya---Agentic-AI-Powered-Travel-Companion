# Architecture overview

Travya is a single-page web app in front of one FastAPI service. The API owns all data access, all
model calls and all calls to third-party services; the browser talks only to the API, to Firebase
Authentication and to the map tile server.

## System context (C4 level 1)

```mermaid
flowchart LR
    traveler(["Traveler<br/>signed in or anonymous demo"])
    travya["Travya<br/>plans trips with AI agents,<br/>maps them, simulates bookings"]
    firebase["Firebase Authentication<br/>accounts and ID tokens"]
    gemini["Gemini API<br/>generation and embeddings"]
    osm["OpenStreetMap services<br/>Nominatim, Photon, Overpass,<br/>OSRM or OpenRouteService"]
    content["Content sources<br/>Open-Meteo, Wikivoyage, Wikipedia,<br/>Unsplash, Wikimedia Commons"]
    tiles["OpenFreeMap<br/>vector map tiles"]

    traveler -- "plans trips, chats, confirms bookings" --> travya
    traveler -- "signs in" --> firebase
    traveler -- "loads tiles" --> tiles
    travya -- "verifies ID tokens" --> firebase
    travya -- "prompts, embeddings" --> gemini
    travya -- "geocoding, places, routes" --> osm
    travya -- "weather, guides, photos" --> content
```

## Containers (C4 level 2)

```mermaid
flowchart TB
    browser(["Browser"])

    subgraph travya["Travya"]
        spa["Web app<br/>React 19, Vite, TanStack Router and Query,<br/>Chakra UI v3, MapLibre<br/>Cloudflare Pages"]
        api["API<br/>FastAPI, Google ADK, SQLModel<br/>Cloud Run, scales 0 to 1"]
        migrate["Migration job<br/>Alembic, same image as the API<br/>Cloud Run job"]
        db[("Database<br/>Postgres 17 + pgvector<br/>Neon")]
        cache[("Cache and counters<br/>Redis<br/>Upstash")]
        files[("Trip documents<br/>Cloud Storage")]
    end

    firebase["Firebase Authentication"]
    gemini["Gemini API"]
    external["Open data services"]

    browser -- "HTTPS" --> spa
    browser -- "REST and SSE, Bearer ID token" --> api
    browser -- "sign in" --> firebase
    browser -- "signed download URL" --> files
    api -- "SQL, vector search" --> db
    api -- "rate limits, LLM budget, HTTP cache" --> cache
    api -- "objects" --> files
    api -- "token verification" --> firebase
    api -- "agents, embeddings" --> gemini
    api -- "cached, rate-limited HTTP" --> external
    migrate -- "DDL" --> db
```

Locally the same containers run in Docker Compose: `pgvector/pgvector:pg17` for Neon,
`redis:8-alpine` for Upstash, the Firebase Auth emulator, local disk for Cloud Storage and nginx
(`frontend/nginx.conf`) or the Vite dev server for Cloudflare Pages.

## Inside the API

```mermaid
flowchart LR
    routers["api/v1<br/>routers"] --> deps["api/deps.py<br/>auth, limits, session"]
    routers --> services["services<br/>use cases"]
    services --> repos["repositories<br/>owner-scoped queries"]
    repos --> models["models<br/>SQLModel tables"]
    services --> agents["agents<br/>ADK pipeline, assistant"]
    agents --> llm["llm/client.py<br/>Gemini with fallback"]
    agents --> ports["integrations/ports.py<br/>protocols"]
    services --> ports
    ports --> adapters["adapters and fakes<br/>selected by registry.py"]
```

| Package | Responsibility |
|---|---|
| `app/main.py` | App factory, lifespan (logging, Sentry, Firebase, cache, HTTP client, integrations, limiter, ADK session service), CORS, request IDs, security headers |
| `app/core/` | Settings, async engine, domain errors and problem+json handlers, structured logging, rate limiter, Firebase token verification |
| `app/api/v1/` | Thin routers: validate input, call one service, map to response schemas |
| `app/services/` | Use cases: trips, planning, chat, documents, notes, feedback, knowledge base, users |
| `app/repositories/` | `ScopedRepository` and one subclass per table; every query carries the owner scope |
| `app/agents/` | The ADK planning pipeline, its prompts, scouts and checks; the travel assistant; SSE event model |
| `app/llm/` | Gemini model with retries and fallback, safety settings, embeddings |
| `app/integrations/` | Ports, adapters for each provider, fakes, the shared HTTP client, cache TTLs, the registry |
| `app/models/`, `app/schemas/` | Tables, and the request, response and structured-output models |

Routers never build error responses and never touch the database directly. Services raise domain
errors (`NotFound`, `Conflict`, `RateLimited`, ...) that `core/errors.py` turns into
`application/problem+json`.

## Request lifecycle

An authenticated request, for example `PATCH /api/v1/trips/{trip_id}`:

```mermaid
sequenceDiagram
    autonumber
    participant B as Browser
    participant FA as Firebase Auth
    participant MW as Middleware
    participant D as Dependencies
    participant S as TripService
    participant R as TripRepository
    participant DB as Postgres

    B->>FA: sign in (email, Google or anonymous)
    FA-->>B: ID token (JWT, refreshed by the SDK)
    B->>MW: PATCH /api/v1/trips/ID with Authorization Bearer token
    MW->>MW: request ID, CORS, security headers
    MW->>D: resolve route dependencies
    D->>D: verify_id_token with firebase-admin
    D->>D: limiter.hit RATE_LIMIT_DEFAULT for this uid
    D->>DB: get or create the users row for this uid
    D->>S: TripService bound to the session and user
    S->>R: get(trip_id) scoped to owner_id = user.id
    R->>DB: SELECT ... WHERE id = ? AND owner_id = ?
    alt missing or owned by someone else
        R-->>B: 404 problem+json, Trip not found
    else owned by the caller
        S->>R: update(changes)
        S->>DB: COMMIT
        S-->>B: 200 TripDetail with X-Request-ID
    end
```

1. **Identity.** The SPA signs in with the Firebase SDK and sends the ID token as a bearer token.
   `get_principal` verifies it (signature, audience, expiry, 10 s clock skew) and builds a
   `Principal` (uid, email, anonymous flag, `admin` custom claim).
2. **Rate limit.** `get_current_user` spends one unit of the caller's `RATE_LIMIT_DEFAULT` window,
   then loads or creates the local `users` row. An anonymous demo account that is later upgraded keeps
   its uid, so the row and all its data carry over.
3. **Route limits.** Expensive routes add their own limit (`rate_limit("6/hour", "plan")`) and the
   planning and chat services spend one unit of the global daily LLM budget before the stream opens.
4. **Service and repository.** The service builds repositories bound to the user (or to a trip that
   was loaded through the user's repository). A foreign id and a missing id both raise `NotFound`.
5. **Response.** Errors become problem+json; every response carries `X-Request-ID`, which also tags
   every log line for that request.

Unauthenticated routes are limited to `/api/v1/health/*` and the OpenAPI documents.

## Streaming

Planning and chat answer with `text/event-stream` (sse-starlette). Validation, ownership checks, rate
limits and the budget run before the stream opens, so those failures are plain HTTP errors; once the
stream is open, failures arrive as `error` events. The event format is in [the API reference](../api.md#server-sent-events)
and the event sequence in [Agents](agents.md#one-planning-run).
