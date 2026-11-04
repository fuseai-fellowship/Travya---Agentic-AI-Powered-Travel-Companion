# API reference

The API is versioned under `/api/v1` and documented by the OpenAPI document that FastAPI generates
from the code.

| URL (local) | What |
|---|---|
| <http://localhost:8000/api/v1/docs> | Swagger UI: try requests in the browser |
| <http://localhost:8000/api/v1/redoc> | ReDoc |
| <http://localhost:8000/api/v1/openapi.json> | The OpenAPI document |

To call protected endpoints from Swagger UI, get an ID token (see
[Getting started](getting-started.md#firebase-auth-emulator)), press **Authorize** and paste it.
Operation ids are `<tag>-<function>`, for example `trips-plan_trip`; the typed frontend client is
generated from them (`make client`).

## Conventions

- **Authentication**: `Authorization: Bearer <Firebase ID token>` on every endpoint except
  `/health/*`. The first authenticated request creates the user's profile.
- **Ownership**: ids of resources that belong to someone else answer `404`, exactly like ids that do
  not exist.
- **Pagination**: trips, notes, conversations and messages return `{"items": [...], "total": n,
  "limit": n, "offset": n}` and accept `limit` and `offset`.
- **Request IDs**: every response has `X-Request-ID`; send your own (a UUID4) to correlate client and
  server logs, otherwise the API generates one.
- **Rate limits**: `429` with `Retry-After` (seconds). Every authenticated request counts against
  `RATE_LIMIT_DEFAULT` (120 per minute); some routes add their own limit below.
- **Streaming**: planning and chat answer with `text/event-stream`.

## Endpoints

### health

| Method | Path | Notes |
|---|---|---|
| `GET` | `/health/live` | Liveness: the process is up. No auth. |
| `GET` | `/health/ready` | Readiness: runs `SELECT 1`; `503 {"status": "unavailable"}` when the database does not answer. No auth. |

### account

| Method | Path | Notes |
|---|---|---|
| `GET` | `/me` | Profile, including `is_anonymous` and `is_admin` |
| `PATCH` | `/me` | `display_name`, `home_city`, `currency` |
| `DELETE` | `/me` | Deletes files, all rows the user owns and the Firebase account. `204` |
| `GET` | `/me/usage` | `{"llm_runs_remaining_today": n}`: the global daily budget left |

### notes

| Method | Path | Notes |
|---|---|---|
| `GET` | `/notes` | Paginated (`limit` 1–100, default 50); filter with `trip_id`. Pinned first, then most recently updated. |
| `POST` | `/notes` | `title`, `content`, `color`, `is_pinned`, optional `trip_id` (must be the user's). `201` |
| `PATCH` | `/notes/{note_id}` | Partial update |
| `DELETE` | `/notes/{note_id}` | `204` |

### documents

| Method | Path | Notes |
|---|---|---|
| `GET` | `/documents` | Newest first; filter with `trip_id` |
| `POST` | `/documents` | Multipart: `file` (PDF, PNG, JPEG or WebP, detected from the file's bytes; at most `MAX_UPLOAD_MB`), optional `trip_id`. Limit 30 per hour. `201` |
| `GET` | `/documents/{document_id}/download` | With Cloud Storage: `{"url": "<signed URL>", "expires_in": 600}`. With local storage: the file itself as an attachment, `Cache-Control: private, no-store`. |
| `DELETE` | `/documents/{document_id}` | Deletes the file and the row. `204` |

### feedback

| Method | Path | Notes |
|---|---|---|
| `POST` | `/feedback` | `target_type` (`trip_plan` or `message`), `target_id`, `rating` 1–5, optional `comment`. One per user and target; posting again updates it. |

### trips

| Method | Path | Notes |
|---|---|---|
| `GET` | `/trips` | Paginated (`limit` 1–100, default 20); filter with `status` and `q` (title or destination). Latest start date first. |
| `POST` | `/trips` | Creates a trip (at most 21 days); geocodes the destination and picks a cover photo. `201` |
| `GET` | `/trips/{trip_id}` | Trip with its stored `plan` (summary, days, tips, sources, review) |
| `PATCH` | `/trips/{trip_id}` | Partial update, including `status` |
| `DELETE` | `/trips/{trip_id}` | Deletes the trip, its items, bookings, photos and documents. `204` |
| `POST` | `/trips/{trip_id}/plan` | Runs the planning agents and streams their events (SSE). Body: `{"instructions": "..."}` (optional, at most 1,000 characters). Limit `RATE_LIMIT_PLAN` (6 per hour) and one unit of the daily LLM budget. |
| `GET` | `/trips/{trip_id}/itinerary` | Items ordered by day, position and time |
| `POST` | `/trips/{trip_id}/itinerary` | Adds a user item; `day` must be within the trip. `201` |
| `PATCH` | `/trips/{trip_id}/itinerary/{item_id}` | Partial update |
| `DELETE` | `/trips/{trip_id}/itinerary/{item_id}` | `204` |
| `GET` | `/trips/{trip_id}/bookings` | Quotes and bookings, ordered by kind, then amount |
| `POST` | `/trips/{trip_id}/bookings/{booking_id}/confirm` | Confirms a quoted booking (simulated) and cancels the other open quotes of the same kind. `409` if it is not `quoted`. |
| `POST` | `/trips/{trip_id}/bookings/{booking_id}/cancel` | `409` if already cancelled |
| `GET` | `/trips/{trip_id}/photos` | Stored photos with author and source |
| `POST` | `/trips/{trip_id}/photos/refresh` | Replaces the photos from the destination and the itinerary's sights and activities. Limit 10 per hour. |
| `GET` | `/trips/{trip_id}/weather` | Daily weather for the trip dates (forecast or climate estimate) |
| `GET` | `/trips/{trip_id}/map` | GeoJSON `FeatureCollection`: one `stop` point per located item, one `route` line per day (walking when the day's stops are within 6 km, driving otherwise), `center`, `bbox` and `attribution` |

### chat

| Method | Path | Notes |
|---|---|---|
| `GET` | `/conversations` | Paginated (`limit` 1–100, default 30); `archived=true` for the archive. Favourites first, then most recent. |
| `POST` | `/conversations` | Optional `title` and `trip_id` (gives the assistant that trip as context). `201` |
| `PATCH` | `/conversations/{conversation_id}` | `title`, `is_archived`, `is_favorite`, `trip_id` |
| `DELETE` | `/conversations/{conversation_id}` | Deletes the messages and the ADK session. `204` |
| `GET` | `/conversations/{conversation_id}/messages` | Paginated (`limit` 1–200, default 100), oldest first |
| `POST` | `/conversations/{conversation_id}/messages` | `{"content": "..."}` (1–4,000 characters). Streams the assistant's reply (SSE). Limit `RATE_LIMIT_CHAT` (40 per hour) and one unit of the daily LLM budget. |

### explore

| Method | Path | Notes |
|---|---|---|
| `GET` | `/explore/places` | Destination autocomplete (Photon): `q` 2–100 characters, `limit` 1–10 (default 6). Limit 120 per minute. |
| `GET` | `/explore/guide` | Destination guide (Wikivoyage, Wikipedia as fallback) with `url`, `source` and `license`; `404` when there is none |

## Errors

Every error raised by the application is an [RFC 9457](https://www.rfc-editor.org/rfc/rfc9457)
problem document with media type `application/problem+json` (`backend/app/core/errors.py`). Stack
traces never reach clients.

```json
{
  "type": "about:blank",
  "title": "Not found",
  "status": 404,
  "detail": "Trip not found",
  "instance": "/api/v1/trips/3f6c2a4e-8d1b-4c39-9a57-1f0e6b2d7c80"
}
```

Validation failures add the individual errors:

```json
{
  "type": "about:blank",
  "title": "Invalid input",
  "status": 422,
  "detail": "Request validation failed",
  "instance": "/api/v1/trips",
  "errors": [
    {"loc": ["body", "currency"], "msg": "String should match pattern '^[A-Z]{3}$'", "type": "string_pattern_mismatch"}
  ]
}
```

| Status | `title` | When | Extra header |
|---|---|---|---|
| 401 | Not authenticated | Missing, invalid or expired ID token | `WWW-Authenticate: Bearer` |
| 403 | Forbidden | An admin-only dependency without the `admin` claim | |
| 404 | Not found | Missing resource, or one that belongs to another user | |
| 409 | Conflict | Booking state does not allow the transition | |
| 422 | Invalid input | Schema validation (with `errors`) or a domain rule: dates, file type or size | |
| 429 | Too many requests | A rate limit was reached | `Retry-After` |
| 503 | Demo limit reached | The global daily LLM budget is spent | |
| 503 | Upstream service unavailable | A third-party service stayed unreachable after retries | |
| 500 | Internal server error | Anything unexpected; logged with the request id | |

Requests to unknown paths or with an unsupported method get FastAPI's default `{"detail": ...}` body.

## Server-Sent Events

`POST /trips/{trip_id}/plan` and `POST /conversations/{conversation_id}/messages` return
`text/event-stream`. Checks that can fail (authentication, ownership, rate limits, the daily budget)
run before the stream opens and fail as normal problem+json responses. After that, every event is one
`AgentEvent` (`backend/app/agents/events.py`):

```text
event: progress
data: {"agent":"places_scout","kind":"progress","message":"Found 45 places on OpenStreetMap.","data":{"places":[{"name":"Durbar Square","category":"attraction","lat":27.7045,"lon":85.3076}]}}
```

| Field | Type | Meaning |
|---|---|---|
| `agent` | string | `travya` (the run itself), a pipeline agent (`weather_scout`, `places_scout`, `guide_scout`, `offers_scout`, `planner`, `critic`, `quality_gate`, `reviser`) or `assistant` |
| `kind` | string | `started`, `progress`, `result`, `token`, `error` or `done`; also the SSE `event` name |
| `message` | string | Human-readable text; for `token`, the next chunk of the answer |
| `data` | object or null | Structured payload, for example scout previews, critic issues, or ids on `done` |

The stream ends after a `done` or an `error` event from `travya` or `assistant`. A comment ping is sent
every 15 seconds to keep proxies from closing the connection, and `X-Accel-Buffering: no` disables
proxy buffering. The per-agent event sequence is described in
[Agents](architecture/agents.md#one-planning-run).

Browsers' `EventSource` cannot send a POST body or an `Authorization` header, so clients use a
fetch-based SSE reader. From a terminal:

```sh
curl -N -X POST "http://localhost:8000/api/v1/trips/$TRIP_ID/plan" \
  -H "Authorization: Bearer $TOKEN" -H 'Content-Type: application/json' -d '{}'
```
