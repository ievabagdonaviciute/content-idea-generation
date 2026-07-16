.PHONY: help db-up db-down api-install api-migrate api-seed api-dev api-test api-lint api-typecheck web-install web-dev web-build web-lint web-typecheck sync-notion purge-data

help:
	@echo "make db-up            start Postgres+pgvector via Docker Compose"
	@echo "make db-down          stop Postgres"
	@echo "make api-install      create venv and install backend deps"
	@echo "make api-migrate      run Alembic migrations"
	@echo "make api-seed         seed demonstration fixtures"
	@echo "make api-dev          run the FastAPI dev server"
	@echo "make api-test         run backend tests"
	@echo "make api-lint         run ruff"
	@echo "make api-typecheck    run mypy"
	@echo "make web-install      install frontend deps"
	@echo "make web-dev          run the Next.js dev server"
	@echo "make web-build        build the frontend"
	@echo "make web-lint         run frontend lint"
	@echo "make web-typecheck    run frontend type-check"
	@echo "make sync-notion      run the Notion sync CLI command"
	@echo "make purge-data       delete all locally stored personal data"

db-up:
	docker compose up -d db

db-down:
	docker compose down

api-install:
	cd apps/api && python3 -m venv .venv && . .venv/bin/activate && pip install -e ".[dev]"

api-migrate:
	cd apps/api && . .venv/bin/activate && alembic upgrade head

api-seed:
	cd apps/api && . .venv/bin/activate && python -m app.cli seed

api-dev:
	cd apps/api && . .venv/bin/activate && uvicorn app.main:app --reload --port 8000

api-test:
	cd apps/api && . .venv/bin/activate && pytest

api-lint:
	cd apps/api && . .venv/bin/activate && ruff check .

api-typecheck:
	cd apps/api && . .venv/bin/activate && mypy app

web-install:
	cd apps/web && npm install

web-dev:
	cd apps/web && npm run dev

web-build:
	cd apps/web && npm run build

web-lint:
	cd apps/web && npm run lint

web-typecheck:
	cd apps/web && npm run typecheck

sync-notion:
	cd apps/api && . .venv/bin/activate && python -m app.cli sync-notion

purge-data:
	cd apps/api && . .venv/bin/activate && python -m app.cli purge-local-data
