PYTHON ?= .venv/bin/python
SYSTEM_PYTHON ?= python3
PYTEST ?= $(PYTHON) -m pytest
RUFF ?= $(PYTHON) -m ruff
PYRIGHT ?= $(PYTHON) -m pyright
ALEMBIC ?= PYTHONPATH=libs/db/src $(PYTHON) -m alembic
COMPOSE ?= docker compose
NPM ?= npm
COMPOSE_BASE := -f docker-compose.yml
COMPOSE_DEV := -f docker-compose.yml -f docker-compose.dev.yml
PROJECT_NAME ?= gridlens-local
BUILD ?=
POSTGRES_HOST ?= 127.0.0.1
POSTGRES_PORT ?= 5432
POSTGRES_DB ?= gridlens_dev
POSTGRES_SUPERUSER ?= gridlens
POSTGRES_SUPERUSER_PASSWORD ?= gridlens_local
POSTGRES_MIGRATOR_USER ?= gridlens_migrator
POSTGRES_MIGRATOR_PASSWORD ?= gridlens_migrator_local
POSTGRES_APP_USER ?= gridlens_app
POSTGRES_APP_PASSWORD ?= gridlens_app_local

.PHONY: setup setup-frontend dev dev-gateway down reset-local-state purge test test-backend test-frontend test-contracts test-libs test-local-db lint typecheck format migrate seed run run-identity-tenant run-frontend

setup: setup-frontend
	@printf '%s\n' 'GridLens local setup'
	@test -f README.md
	@test -f .env.example
	@test -f docker-compose.yml
	@test -f docker-compose.dev.yml
	@test -f pyproject.toml
	@if ! test -x .venv/bin/python; then \
		printf '%s\n' 'Creating .venv...'; \
		$(SYSTEM_PYTHON) -m venv .venv; \
	fi
	$(PYTHON) -m pip install --upgrade pip
	$(PYTHON) -m pip install -e '.[dev]'
	@printf '%s\n' 'Optional: copy .env.example to .env and adjust development-only placeholders.'
	@printf '%s\n' 'Run make test for offline checks or make dev for the local runtime.'

setup-frontend:
	@if test -f frontend/package-lock.json; then \
		cd frontend && $(NPM) ci; \
	fi

dev:
	$(COMPOSE) $(COMPOSE_DEV) up $(BUILD) -d

dev-gateway:
	$(COMPOSE) $(COMPOSE_DEV) up --build identity-tenant-service kong

run: dev

run-identity-tenant:
	PYTHONPATH=services/identity-tenant-service/src $(PYTHON) -m uvicorn gridlens_identity_tenant_service.main:app --host 127.0.0.1 --port $${API_PORT:-8000}

down:
	$(COMPOSE) $(COMPOSE_BASE) down

reset-local-state:
	$(COMPOSE) $(COMPOSE_BASE) down --volumes --remove-orphans

purge:
	$(COMPOSE) $(COMPOSE_DEV) down --volumes --remove-orphans --rmi local

test: test-backend test-frontend
	@printf '%s\n' 'Default offline tests completed.'

test-backend:
	$(PYTEST)

test-contracts:
	$(PYTEST) libs/contracts/tests

test-libs:
	$(PYTEST) libs

test-frontend:
	cd frontend && $(NPM) test -- --run

run-frontend:
	cd frontend && $(NPM) run dev

test-local-db:
	@printf '%s\n' 'Checking local PostgreSQL, app schema, PGVector, and role split...'
	$(COMPOSE) $(COMPOSE_BASE) exec -T postgres psql \
		-U "$${POSTGRES_SUPERUSER:-gridlens}" \
		-d "$${POSTGRES_DB:-gridlens_dev}" \
		-v ON_ERROR_STOP=1 \
		-c "select extname from pg_extension where extname = 'vector';" \
		-c "select schema_name from information_schema.schemata where schema_name = 'app';" \
		-c "select rolname from pg_roles where rolname in ('gridlens_migrator', 'gridlens_app') order by rolname;"
	$(COMPOSE) $(COMPOSE_BASE) exec -T -e PGPASSWORD="$(POSTGRES_MIGRATOR_PASSWORD)" postgres psql \
		-U "$(POSTGRES_MIGRATOR_USER)" \
		-d "$${POSTGRES_DB:-gridlens_dev}" \
		-v ON_ERROR_STOP=1 \
		-c "create table if not exists app.local_migrator_smoke_check (id integer primary key);" \
		-c "drop table app.local_migrator_smoke_check;"
	@if $(COMPOSE) $(COMPOSE_BASE) exec -T -e PGPASSWORD="$(POSTGRES_APP_PASSWORD)" postgres psql \
		-U "$(POSTGRES_APP_USER)" \
		-d "$${POSTGRES_DB:-gridlens_dev}" \
		-v ON_ERROR_STOP=1 \
		-c "create table app.local_app_role_must_not_create (id integer primary key);"; then \
		printf '%s\n' 'gridlens_app unexpectedly created schema objects.' >&2; \
		exit 1; \
	else \
		printf '%s\n' 'gridlens_app cannot create schema objects.'; \
	fi

lint:
	$(RUFF) check services libs tests

typecheck:
	$(PYRIGHT)

format:
	@printf '%s\n' 'No formatter is configured yet. Future Python and frontend formatters should run here.'

migrate:
	$(ALEMBIC) -c infra/db/alembic.ini upgrade head

seed:
	PYTHONPATH=libs/db/src $(PYTHON) -m gridlens_db.seed
