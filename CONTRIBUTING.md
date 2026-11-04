# Contributing

## Branches

| Branch | Role | Merges in by |
|---|---|---|
| `dev` | Default branch; integration | Squash merge of feature PRs |
| `main` | Production; every push deploys | Merge commit of a release PR from `dev` (or `hotfix/*`) |

1. Branch from `dev`: `feat/<topic>`, `fix/<topic>`, `docs/<topic>`, ...
2. Open a PR into `dev`. The single required check is **ci-ok**; it passes when every CI job that the
   change touches passes.
3. To release, open a PR from `dev` into `main` and merge it with a merge commit (not squash, so the
   two branches keep a shared history). CI rejects PRs into `main` from any other branch except
   `hotfix/*` and the release-please branch.
4. A push to `main` deploys (`.github/workflows/deploy.yml`) and release-please opens or updates a
   release PR with the changelog. Merging that PR tags the release.
5. After a hotfix, merge `main` back into `dev`.

## Commit messages

[Conventional Commits](https://www.conventionalcommits.org/): `type(scope): summary`, for example
`feat(planner): add a budget step` or `fix(api): return 404 for foreign trips`.
Types: `feat`, `fix`, `perf`, `refactor`, `docs`, `test`, `build`, `ci`, `chore`, `security`.
Breaking changes: `feat!: ...` or a `BREAKING CHANGE:` footer. Squash merges use the PR title, so
the PR title must follow the same format.

## Local setup

Requirements: Docker with Compose v2.24+, [uv](https://docs.astral.sh/uv/), Node 24, and
optionally [pre-commit](https://pre-commit.com/) and Terraform.

```sh
cp .env.example .env              # works as is: offline integrations, local emulators
make up                           # db, redis, Auth emulator, migrations, API :8000, web :5173
make logs s=api                   # follow one service
make down
```

| URL | What |
|---|---|
| http://localhost:5173 | Web app (Vite, hot reload) |
| http://localhost:8000/api/v1/docs | API docs (uvicorn, hot reload) |
| http://localhost:9099 | Firebase Auth emulator (project `demo-travya`) |
| localhost:5433 | Postgres (`travya` / `travya_test`, user and password `travya`) |
| localhost:6379 | Redis |

Backend and frontend tooling run on the host:

```sh
(cd backend && uv sync) && (cd frontend && npm ci)
pre-commit install                # ruff, biome, gitleaks and file hygiene on every commit
make lint                         # ruff, mypy, biome, tsc
make fmt
make test                         # pytest (needs `make up` for Postgres) and vitest
make e2e                          # Playwright against the production images, in a separate compose project
```

Database migrations:

```sh
make revision m="add trip notes"  # autogenerate from the models; review the file before committing
make migrate                      # apply to the compose database
```

API client: after changing routes or schemas, run `make client` (exports the OpenAPI document and
regenerates the typed client in `frontend/`), and commit the result.

## Infrastructure

`infra/terraform` defines the Google Cloud side (Cloud Run, Artifact Registry, Secret Manager,
Workload Identity Federation, storage, budget). See the comments in `variables.tf` and
`terraform.tfvars.example`; `make tf-plan` / `make tf-apply` wrap the usual commands.
