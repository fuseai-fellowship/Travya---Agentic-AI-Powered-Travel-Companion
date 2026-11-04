# Deployment

Production runs on free tiers: the API on Cloud Run, Postgres on Neon, Redis on Upstash, the web app
on Cloudflare Pages, authentication on Firebase, trip documents on Cloud Storage. Terraform
(`infra/terraform/`) owns the Google Cloud side, including each service's configuration;
`.github/workflows/deploy.yml` only ships new images. The reasoning is in
[ADR 0004](../decisions/0004-cloud-run-free-tier.md).

## Production architecture

```mermaid
flowchart TB
    gh["GitHub Actions<br/>deploy.yml"]
    subgraph cloudflare["Cloudflare"]
        pages["Pages project travya<br/>static SPA, CSP in _headers"]
    end
    subgraph gcp["Google Cloud project, us-central1"]
        wif["Workload Identity Federation<br/>pool github, provider travya-deploy"]
        ar["Artifact Registry travya<br/>keeps the 2 newest images"]
        run["Cloud Run service travya-api<br/>0 to 1 instance, 1 vCPU, 512 MiB,<br/>40 concurrent requests, 300 s timeout"]
        job["Cloud Run job travya-migrate<br/>alembic upgrade head"]
        sm["Secret Manager"]
        bucket[("Cloud Storage<br/>PROJECT-travya-documents")]
        budget["Billing budget<br/>alerts at 50, 90, 100 %"]
    end
    fb["Firebase Authentication"]
    neon[("Neon Postgres + pgvector")]
    upstash[("Upstash Redis")]

    gh -- "OIDC token" --> wif
    gh -- "push image" --> ar
    gh -- "update and execute" --> job
    gh -- "deploy revision" --> run
    gh -- "wrangler pages deploy" --> pages
    ar --> run
    ar --> job
    sm -. "env vars at instance start" .-> run
    sm -. "env vars at execution" .-> job
    run --> bucket
    run --> neon
    run --> upstash
    run --> fb
    job --> neon
```

| Component | Configuration | Why it stays free |
|---|---|---|
| Cloud Run `travya-api` | Min 0, max 1 instance; 1 vCPU, 512 MiB; CPU only while serving requests; startup boost; 300 s request timeout; startup and liveness probes on `/api/v1/health/live`; public invoker | Scales to zero between visits |
| Cloud Run job `travya-migrate` | Same image and environment as the API, `alembic upgrade head`, no retries | Runs once per deploy |
| Artifact Registry `travya` | Cleanup policy keeps the 2 newest versions | Stays under the 0.5 GB free storage |
| Cloud Storage | Private, uniform access, public access prevention, no soft delete, objects deleted after 365 days | Regional bucket in us-central1 |
| Secret Manager | `gemini-api-key`, `database-url`, `redis-url`, `unsplash-access-key`, `ors-api-key`, `sentry-dsn` | A handful of secrets |
| Neon | Postgres 17; the baseline migration enables `vector`; `?sslmode=require` | Free plan; compute suspends when idle |
| Upstash | Redis over TLS (`rediss://`) | Free plan |
| Cloudflare Pages | Project `travya`, direct upload | Free plan |
| Billing budget | $1 per month, alerts at 50, 90 and 100 % | Early warning if anything starts to cost |

The service's environment comes from Terraform: `ENVIRONMENT=production`, `LOG_JSON=true`,
`FIREBASE_PROJECT_ID`, `GEMINI_MODEL`, `STORAGE_BACKEND=gcs`, `GCS_BUCKET`, `FRONTEND_ORIGINS`, plus the
wired secrets. Terraform ignores image changes, so deploys and `terraform apply` do not fight.

## One-time bootstrap

1. **Accounts.** A Google Cloud project linked to a billing account, with Firebase added to it; a Neon
   project; an Upstash Redis database; a Cloudflare account.
2. **Firebase.** In the Firebase console enable the Email/Password, Google and Anonymous sign-in
   providers, add the Pages domain to the authorised domains, and register a web app to get its API
   key.
3. **Neon.** Create the database. The connection string becomes
   `postgresql+psycopg://USER:PASSWORD@HOST/DB?sslmode=require`. Nothing else is needed: the baseline
   migration enables pgvector and creates the `adk` schema on the first deploy.

4. **Terraform state and first apply** (from `infra/terraform/terraform.tfvars.example`; copy it to
   `terraform.tfvars` and set `project_id` and `billing_account_id`):

    ```sh
    gcloud auth application-default login
    gcloud config set project <project-id>
    gcloud services enable cloudresourcemanager.googleapis.com serviceusage.googleapis.com
    gcloud storage buckets create gs://<project-id>-tfstate --location=us-central1 \
      --uniform-bucket-level-access --public-access-prevention
    gcloud storage buckets update gs://<project-id>-tfstate --versioning
    make tf-init bucket=<project-id>-tfstate
    terraform -chdir=infra/terraform apply -target=google_secret_manager_secret.app
    ```

5. **Secrets.** Add a version to every secret listed in `wired_secrets`; Cloud Run refuses to start
   with an empty secret, so drop optional ones (`sentry-dsn`, `unsplash-access-key`, `ors-api-key`)
   from `wired_secrets` until they have a value.

    ```sh
    printf %s "$VALUE" | gcloud secrets versions add gemini-api-key --data-file=-
    printf %s "$VALUE" | gcloud secrets versions add database-url --data-file=-
    printf %s "$VALUE" | gcloud secrets versions add redis-url --data-file=-
    ```

6. **Apply everything** and read the values the workflow needs:

    ```sh
    make tf-plan && make tf-apply
    terraform -chdir=infra/terraform output github_variables
    ```

    The service and the job start on a placeholder image; the first deploy replaces it.

7. **Cloudflare.** Create a Pages project named `travya` for direct upload, and an API token that can
   edit Cloudflare Pages.
8. **GitHub.** In the `production` environment (or as repository variables) set `GCP_PROJECT_ID`,
   `GCP_REGION`, `WIF_PROVIDER`, `DEPLOY_SA`, `CF_ACCOUNT_ID`, `VITE_FIREBASE_API_KEY`,
   `VITE_FIREBASE_AUTH_DOMAIN`, and optionally `VITE_FIREBASE_PROJECT_ID` (defaults to the GCP project)
   and `VITE_API_URL` (defaults to the Cloud Run URL). Add the secret `CLOUDFLARE_API_TOKEN`, and
   optionally `RELEASE_PLEASE_TOKEN` (a fine-grained token with contents and pull-request write access)
   so that release PRs trigger CI.
9. **Repository settings.** Require the `ci-ok` check on `dev` and `main`, and set Pages to deploy from
   GitHub Actions for this documentation site.
10. **First deploy.** Merge a release PR into `main`, or run the workflow by hand:
    `gh workflow run deploy.yml --ref main`.

If the web app is served from a different origin than `https://travya.pages.dev`, set
`frontend_origins` in `terraform.tfvars`: it drives both the API's CORS allowlist and the bucket's CORS.

## Branches, CI and delivery

```mermaid
flowchart LR
    work["feat/*, fix/*, docs/*"]
    dev["dev<br/>default branch"]
    hotfix["hotfix/*"]
    main["main<br/>production"]
    rp["release-please<br/>release PR"]
    tag["tag vX.Y.Z<br/>and CHANGELOG"]
    subgraph deploy["deploy.yml on every push to main"]
        direction LR
        gate["CI gate<br/>full ci.yml"] --> build["Build the API image once<br/>tagged with the git SHA"]
        build --> migrate["Execute travya-migrate<br/>with that image"]
        migrate --> revision["Deploy the Cloud Run revision"]
        revision --> smoke["Smoke test<br/>/api/v1/health/ready"]
        smoke --> web["Build the SPA once,<br/>deploy to Cloudflare Pages"]
    end

    work -- "PR, ci-ok, squash merge" --> dev
    dev -- "release PR, merge commit" --> main
    hotfix -- "PR, merge commit" --> main
    main -. "merge back after a hotfix" .-> dev
    main -- "push" --> gate
    main -- "push" --> rp
    rp -- "merge" --> tag
```

- **Pull requests** into `dev` or `main` run `ci.yml` and CodeQL. `ci.yml` always runs a gitleaks
  scan of the new commits, and otherwise detects what changed and runs only the relevant jobs:
  backend (Ruff, mypy, a check that the committed `frontend/openapi.json` matches the code, migrations
  on an empty database, pytest with coverage), frontend (Biome, `tsc`, Vitest, build), Playwright end
  to end on the production images, and image builds with Trivy (fails on fixable critical
  vulnerabilities) and a CycloneDX SBOM. The single required check, `ci-ok`, passes when every job
  either passed or was skipped.
- **`main` accepts PRs only from `dev`, `hotfix/*` and release-please branches** (`release-guard`
  job). Releases use merge commits so `dev` and `main` keep a shared history.
- **Deploy** runs on every push to `main`. The image is built once, used first by the migration job
  and then by the new revision, so the code that migrated the schema is the code that serves it. The
  smoke test retries `/api/v1/health/ready` for about a minute. The web build pins the CSP
  `connect-src` in `_headers` to the API's origin before upload.
- **Docs** (`docs.yml`) build with `mkdocs build --strict` on PRs that touch them and publish to GitHub
  Pages from `main`.
- **Dependabot** opens grouped weekly updates against `dev`; **OpenSSF Scorecard** runs weekly and on
  pushes to `dev`.

## Rollback

The API keeps every revision. To send traffic back to the previous one:

```sh
gcloud run revisions list --service travya-api --region "$REGION"
gcloud run services update-traffic travya-api --region "$REGION" --to-revisions <REVISION>=100
# once a fix is deployed
gcloud run services update-traffic travya-api --region "$REGION" --to-latest
```

- Terraform declares 100 % of traffic on the latest revision, so a `terraform apply` while pinned
  sends traffic back to the latest revision.
- Artifact Registry keeps only the two newest images, so the previous revision is the dependable
  rollback target; older revisions may point at deleted images.
- Rolling back the service does not roll back the schema. Migrations must stay compatible with the
  previous release (add first, remove in a later release).
- The web app can be rolled back from the Cloudflare Pages dashboard (Deployments, then Rollback).
- The durable fix is a revert on `dev` released to `main`, or a `hotfix/*` PR into `main`.
