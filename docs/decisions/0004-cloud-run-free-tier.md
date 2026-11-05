# 0004. Host on Cloud Run and managed free tiers

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
