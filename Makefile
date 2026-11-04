# Developer shortcuts. Each target is a thin wrapper over docker compose, uv, npm or terraform.
# `make help` lists them.

SHELL := /bin/bash
.DEFAULT_GOAL := help

COMPOSE   := docker compose
E2E       := OFFLINE_INTEGRATIONS=true docker compose -p travya-e2e -f compose.yaml --profile e2e
TF        := terraform -chdir=infra/terraform
# Host-side tools talk to the compose services through their published ports.
DB_URL      ?= postgresql+psycopg://travya:travya@localhost:5433/travya
TEST_DB_URL ?= postgresql+psycopg://travya:travya@localhost:5433/travya_test

.PHONY: help up down logs migrate revision test lint fmt openapi client e2e tf-init tf-plan tf-apply

help: ## List targets
	@grep -E '^[a-z0-9-]+:.*## ' $(MAKEFILE_LIST) | awk -F':.*## ' '{printf "  %-10s %s\n", $$1, $$2}'

up: ## Start the dev stack (hot reload) in the background
	$(COMPOSE) up -d --build --renew-anon-volumes

down: ## Stop the dev stack (data volume kept)
	$(COMPOSE) down --remove-orphans

logs: ## Follow logs (all services, or s=<service>)
	$(COMPOSE) logs -f --tail=200 $(s)

migrate: ## Apply migrations to the compose database
	$(COMPOSE) run --rm migrate

revision: ## Autogenerate a migration from the models: make revision m="add notes"
	@test -n "$(m)" || { echo 'usage: make revision m="message"'; exit 1; }
	cd backend && DATABASE_URL=$(DB_URL) uv run alembic revision --autogenerate -m "$(m)"

test: ## Backend (pytest, needs `make up`) and frontend (vitest) tests
	cd backend && TEST_DATABASE_URL=$(TEST_DB_URL) uv run pytest && cd ../frontend && npm run test

lint: ## Ruff, mypy, biome and tsc
	cd backend && uv run ruff check . && uv run ruff format --check . && uv run mypy app && cd ../frontend && npm run lint && npm run typecheck

fmt: ## Auto-fix lint findings and format both apps
	cd backend && uv run ruff check --fix . && uv run ruff format . && cd ../frontend && npx biome check --write .

openapi: ## Export the OpenAPI document to frontend/openapi.json
	cd backend && uv run python -m app.scripts.export_openapi > ../frontend/openapi.json

client: openapi ## Regenerate the typed API client from the OpenAPI document
	cd frontend && npm run generate-client

e2e: ## Playwright against the production images (separate compose project, removed afterwards)
	$(E2E) build && $(E2E) run --rm e2e; status=$$?; $(E2E) down -v --remove-orphans; exit $$status

tf-init: ## Initialise Terraform: make tf-init bucket=<state-bucket>
	@test -n "$(bucket)" || { echo 'usage: make tf-init bucket=<gcs-state-bucket>'; exit 1; }
	$(TF) init -backend-config="bucket=$(bucket)"

tf-plan: ## Terraform plan into infra/terraform/tfplan
	$(TF) plan -out=tfplan

tf-apply: ## Apply the saved plan
	$(TF) apply tfplan
