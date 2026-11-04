# Runbook

Commands assume `REGION` is set to the deployment region (`us-central1` by default) and `gcloud`
points at the production project.

## Health checks

| Check | Meaning | Used by |
|---|---|---|
| `GET /api/v1/health/live` | The process answers | Cloud Run startup and liveness probes, the image `HEALTHCHECK` |
| `GET /api/v1/health/ready` | The database answers `SELECT 1`; `503` otherwise | The deploy smoke test, the Compose healthcheck |
| `GET /healthz` on the web container | nginx is up | Compose and the end-to-end stack only |

```sh
URL=$(gcloud run services describe travya-api --region "$REGION" --format 'value(status.url)')
curl -fsS "$URL/api/v1/health/ready"
```

The first request after an idle period starts an instance (Cloud Run scales to zero) and may wake the
Neon compute; expect a few seconds of extra latency.

## Logs and request IDs

Production logs are JSON lines on stdout (`LOG_JSON=true`), one object per event with `event`,
`level`, `logger`, `timestamp` and the event's fields. Every line logged while serving a request
carries `request_id`, the same value the client receives in the `X-Request-ID` response header.

```sh
# everything for one request
gcloud logging read \
  'resource.type="cloud_run_revision" AND resource.labels.service_name="travya-api"
   AND jsonPayload.request_id="<id from X-Request-ID>"' --limit 100 --freshness 1d

# recent upstream trouble
gcloud logging read \
  'resource.labels.service_name="travya-api"
   AND (jsonPayload.event="upstream_gave_up" OR jsonPayload.event="llm_fallback")' \
  --limit 50 --freshness 1d
```

| Event | Meaning |
|---|---|
| `startup` | The app started; shows `environment` and `offline` |
| `upstream_retry`, `upstream_gave_up`, `upstream_error`, `upstream_http_error` | A third-party call was retried, failed for good, or answered with an error |
| `router_fallback`, `photos_fallback` | OpenRouteService or Unsplash failed; the keyless fallback was used |
| `llm_fallback` | The primary Gemini model was overloaded; the fallback model answered |
| `scout_failed` | A research scout failed; the plan continued without it |
| `plan_invalid`, `plan_failed` | A planning run ended without a valid plan; the trip status was restored |
| `chat_failed` | An assistant turn failed |
| `guide_indexed` | A destination guide was embedded into the knowledge base |
| `route_failed`, `cover_photo_failed` | Map routes or a cover photo were skipped |
| `gcs_signing_unavailable` | Downloads fall back to streaming through the API |
| `unhandled_error` | A 500; the line includes the stack trace |

With `SENTRY_DSN` set (secret `sentry-dsn`), errors also go to Sentry, tagged with the environment,
without personal data, with 10 % trace sampling.

## Rate limits and the LLM budget

| Setting | Default | Scope |
|---|---|---|
| `RATE_LIMIT_DEFAULT` | `120/minute` | Per user, every authenticated request (moving window) |
| `RATE_LIMIT_PLAN` | `6/hour` | Per user, planning runs |
| `RATE_LIMIT_CHAT` | `40/hour` | Per user, chat messages |
| `LLM_DAILY_REQUEST_BUDGET` | `400` | All users together, planning runs plus chat messages, fixed 24-hour window |

Upload (30 per hour), photo refresh (10 per hour) and autocomplete (120 per minute) limits are set in
the routers.

Counters live in Redis, so they are shared by instances and survive restarts. The budget window starts
with the first run after the previous window expired; the API answers `503 Demo limit reached` until it
expires. `GET /api/v1/me/usage` shows how many runs are left.

To change a value in production, add it to `local.plain_env` in `infra/terraform/main.tf` and apply;
a new revision picks it up. A one-off `gcloud run services update travya-api --update-env-vars ...`
also works but is reverted by the next `terraform apply`.

Size the budget from the model's free-tier daily request quota: one planning run makes up to five
generation calls (planner, two critic and two reviser calls) plus embedding calls, and a chat turn up to
eight.

## Rotating keys

Secrets are read when an instance starts (`version = "latest"`), so a rotation is: add a version, start
new instances, disable the old version, revoke the old credential.

```sh
printf %s "$NEW_VALUE" | gcloud secrets versions add gemini-api-key --data-file=-
gh workflow run deploy.yml --ref main        # new revision, new instances, migrate job included
gcloud secrets versions list gemini-api-key
gcloud secrets versions disable <old-version> --secret gemini-api-key
```

| Credential | Where to rotate it | Then |
|---|---|---|
| Gemini API key (`gemini-api-key`) | Google AI Studio | Add the version, redeploy, delete the old key in AI Studio |
| Database URL (`database-url`) | Neon: reset the role's password | Add the version, redeploy |
| Redis URL (`redis-url`) | Upstash: reset the password | Add the version, redeploy |
| Unsplash, OpenRouteService, Sentry | The provider's dashboard | Add the version, redeploy |
| `CLOUDFLARE_API_TOKEN` | Cloudflare API tokens | `gh secret set CLOUDFLARE_API_TOKEN --env production` |
| `RELEASE_PLEASE_TOKEN` | GitHub fine-grained tokens | `gh secret set RELEASE_PLEASE_TOKEN` |
| Google Cloud deploy credentials | Nothing to rotate: Workload Identity Federation issues short-lived tokens per run | |

If a key leaks, revoke it at the provider first; rotation alone leaves the leaked key valid.

## Common failures

| Symptom | Likely cause | Fix |
|---|---|---|
| Revision fails to start: `Missing production settings: ...` | A required secret or setting is missing in staging or production | Add the secret version, or wire the secret in `wired_secrets` |
| Cloud Run rejects the revision because of a secret | A wired secret has no version | Add a version, or remove it from `wired_secrets` |
| `/health/ready` returns 503 | Neon unreachable or suspended, wrong `DATABASE_URL`, missing `?sslmode=require` | Check the secret and Neon's status; the pool reconnects on its own (`pool_pre_ping`) |
| Every request answers 401 | `FIREBASE_PROJECT_ID` differs from the project that issued the tokens, or (locally) the API is not pointed at the emulator | Align the project id; locally set `FIREBASE_AUTH_EMULATOR_HOST` |
| Browser shows CORS errors | The web origin is not in `FRONTEND_ORIGINS` | Update `frontend_origins` in Terraform and apply |
| `503 Demo limit reached` | The daily LLM budget is spent | Wait for the window, or raise `LLM_DAILY_REQUEST_BUDGET` |
| `429` with `Retry-After` | A per-user limit | Expected; tune the `RATE_LIMIT_*` values if real users hit it |
| Planning ends with "Planning failed because an AI or data service is unavailable" | Gemini quota or outage, or an upstream failure outside a scout | Search `plan_failed` and `llm_fallback`; check the AI Studio quota |
| Planning ends with "The planner returned an incomplete plan" | The final plan failed `TripPlan` validation | Search `plan_invalid`; re-run the plan |
| A trip stays in `planning` | The client disconnected mid-run, which cancels the stream before the status is restored | Re-plan the trip, or `PATCH` its `status` |
| Scout says "Could not reach this source" | Overpass, Open-Meteo or Wikivoyage is down or rate-limiting | None needed; the plan continues; check `upstream_gave_up` |
| Nominatim answers 403 or 429 | Missing or generic `HTTP_USER_AGENT`, or too many requests | Keep an identifying agent with a contact; the 1 request/second limit is per process |
| Downloads stream through the API instead of a signed URL | The credentials cannot sign (`gcs_signing_unavailable`) | The runtime service account needs Token Creator on itself (Terraform grants it) |
| Event streams stop after five minutes | Cloud Run's 300 s request timeout | Planning normally ends well before; raise `timeout` in Terraform if needed |
| Local `make up`: port 5432 in use | A native Postgres | Compose already publishes on 5433; use that port |
| Guide search returns nothing after changing `EMBEDDING_DIM` | The `vector(768)` column no longer matches | Keep 768, or migrate the column and re-embed |
