# 0004. Host on free tiers: Hugging Face Spaces or Cloud Run

- Status: accepted
- Date: 2026-11-04

## Context

The demo must stay online for reviewers at no cost and with no server to look after. The prototype's
deployment targeted a self-hosted VPS behind Traefik with self-hosted CI runners; none of it ever ran.
The API streams Server-Sent Events for up to a few minutes per planning run, and traffic is low and
bursty.

## Decision

- **API**: Cloud Run service `travya-api`, minimum 0 and maximum 1 instance, 1 vCPU and 512 MiB,
  CPU allocated only while serving requests, 40 concurrent requests, 300 s request timeout.
- **Migrations**: Cloud Run job `travya-migrate` with the same image, executed by the deploy workflow
  before each new revision.
- **Data**: Neon (Postgres 17 with pgvector), Upstash (Redis over TLS), Cloud Storage in us-central1
  for documents with a one-year lifecycle.
- **Web**: Cloudflare Pages for the static SPA, with security headers in `_headers`.
- **Auth**: Firebase Authentication.
- **Infrastructure as code**: Terraform with remote state in GCS defines the Google Cloud side,
  including service configuration, secrets (without values), Workload Identity Federation and a $1
  monthly budget alert. Deploys only change the image.
- **Images**: Artifact Registry keeps the two newest images.

## Consequences

- No idle cost and no machines to patch.
- One instance at most bounds the worst-case bill; in-memory planning sessions are safe because a
  run lives on one instance.
- Cold starts add a few seconds after idle periods, and Neon's compute may need to wake as well.
- An SSE stream cannot outlive the 300 s request timeout.
- Rate limits and caches must live in Redis rather than process memory, because instances come and go.
- Several providers means several dashboards and credentials; Terraform and the runbook keep them
  documented.
- Rollback is limited to recent revisions because old images are cleaned up.

## Alternatives considered

- **A small VM**: always on and simple, but it costs money or needs care, and patching is manual.
- **Fly.io or Render**: similar developer experience, but less generous or less predictable free
  tiers, and the rest of the stack is already on Google Cloud.
- **GKE**: far more than one container needs, and not free.
- **Serverless functions** (Vercel, Netlify): short execution limits that do not suit long SSE
  streams or the Python agent runtime.

## Update: Hugging Face Spaces as the default host

Google Cloud requires a non-prepaid card to attach billing, and Cloud Run cannot run without billing.
To keep the demo free and card-free, the API now deploys to a **Hugging Face Docker Space** by default:

- The deploy workflow uploads `backend/` to the Space with the `hf` CLI; the Space builds the same
  `backend/Dockerfile` (prod stage) and serves it on port 8000. A `BUILD_SHA` file lets the workflow
  wait until `/api/v1/health/live` reports the new revision.
- There is no separate migration job, so the container runs `alembic upgrade head` on start
  (`RUN_MIGRATIONS_ON_START=true`, `backend/start.sh`).
- Spaces have no durable disk, so uploaded documents are stored in Postgres
  (`STORAGE_BACKEND=database`, `integrations/storage/database.py`), behind the same storage port.
- Firebase user records are deleted by the client after the API has removed the user's data, since
  the Space has no Google credentials.
- Trade-off: a free Space sleeps after 48 hours without traffic and takes a minute or two to wake;
  it has more CPU and memory than Cloud Run's free allowance.

Both routes stay in `deploy.yml`; each deploy job is skipped until its variables exist.
