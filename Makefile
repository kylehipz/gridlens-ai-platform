PYTHON ?= .venv/bin/python
SYSTEM_PYTHON ?= python3
PYTEST ?= $(PYTHON) -m pytest
RUFF ?= $(PYTHON) -m ruff
PYRIGHT ?= $(PYTHON) -m pyright
COMPOSE ?= docker compose
COMPOSE_BASE := -f docker-compose.yml
COMPOSE_DEV := -f docker-compose.yml -f docker-compose.dev.yml
PROJECT_NAME ?= gridlens-local
BUILD ?=
POSTGRES_HOST ?= 127.0.0.1
POSTGRES_PORT ?= 5432
POSTGRES_DB ?= gridlens_dev
POSTGRES_SUPERUSER ?= gridlens
POSTGRES_SUPERUSER_PASSWORD ?= gridlens_local
POSTGRES_USER ?= gridlens_app
POSTGRES_PASSWORD ?= gridlens_app_local
POSTGRES_CONTAINER_ID ?=

ifeq ($(strip $(POSTGRES_CONTAINER_ID)),)
PSQL_SUPERUSER = PGPASSWORD="$(POSTGRES_SUPERUSER_PASSWORD)" psql -h "$(POSTGRES_HOST)" -p "$(POSTGRES_PORT)" -U "$(POSTGRES_SUPERUSER)" -d "$(POSTGRES_DB)"
PSQL_APP = PGPASSWORD="$(POSTGRES_PASSWORD)" psql -h "$(POSTGRES_HOST)" -p "$(POSTGRES_PORT)" -U "$(POSTGRES_USER)" -d "$(POSTGRES_DB)"
else
PSQL_SUPERUSER = docker exec -e PGPASSWORD="$(POSTGRES_SUPERUSER_PASSWORD)" "$(POSTGRES_CONTAINER_ID)" psql -U "$(POSTGRES_SUPERUSER)" -d "$(POSTGRES_DB)"
PSQL_APP = docker exec -e PGPASSWORD="$(POSTGRES_PASSWORD)" "$(POSTGRES_CONTAINER_ID)" psql -U "$(POSTGRES_USER)" -d "$(POSTGRES_DB)"
endif

.PHONY: setup dev dev-gateway down reset-local-state test test-backend test-frontend test-contracts test-libs test-local-db bootstrap-live-db test-live-db lint typecheck format migrate seed run run-identity-tenant run-frontend

setup:
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

test: test-backend test-frontend
	@printf '%s\n' 'Default offline tests completed.'

test-backend:
	$(PYTEST)

test-contracts:
	$(PYTEST) libs/contracts/tests

test-libs:
	$(PYTEST) libs

test-frontend:
	cd frontend && npm test -- --run

run-frontend:
	cd frontend && npm run dev

test-local-db:
	@printf '%s\n' 'Checking local PostgreSQL, app schema, and PGVector...'
	$(COMPOSE) $(COMPOSE_BASE) exec -T postgres psql \
		-U "$${POSTGRES_SUPERUSER:-gridlens}" \
		-d "$${POSTGRES_DB:-gridlens_dev}" \
		-v ON_ERROR_STOP=1 \
		-c "select extname from pg_extension where extname = 'vector';" \
		-c "select schema_name from information_schema.schemata where schema_name = 'app';"
	$(COMPOSE) $(COMPOSE_BASE) exec -T postgres psql \
		-U "$${POSTGRES_USER:-gridlens_app}" \
		-d "$${POSTGRES_DB:-gridlens_dev}" \
		-v ON_ERROR_STOP=1 \
		-c "create table if not exists app.local_smoke_check (id integer primary key);" \
		-c "drop table app.local_smoke_check;"

bootstrap-live-db:
	@printf '%s\n' 'Bootstrapping live PostgreSQL schema, role, and PGVector...'
	@case "$(POSTGRES_USER)" in ""|*[!A-Za-z0-9_]* ) printf '%s\n' 'POSTGRES_USER must contain only letters, numbers, and underscores' >&2; exit 1;; esac
	@case "$(POSTGRES_PASSWORD)" in ""|*"'"* ) printf '%s\n' "POSTGRES_PASSWORD must be non-empty and must not contain single quotes" >&2; exit 1;; esac
	$(PSQL_SUPERUSER) \
		-v ON_ERROR_STOP=1 \
		-c "DO \$$\$$ BEGIN IF NOT EXISTS (SELECT 1 FROM pg_roles WHERE rolname = '$(POSTGRES_USER)') THEN CREATE ROLE \"$(POSTGRES_USER)\" LOGIN PASSWORD '$(POSTGRES_PASSWORD)'; END IF; END \$$\$$;" \
		-c "CREATE EXTENSION IF NOT EXISTS vector;" \
		-c "CREATE SCHEMA IF NOT EXISTS app AUTHORIZATION \"$(POSTGRES_USER)\";" \
		-c "GRANT CONNECT ON DATABASE \"$(POSTGRES_DB)\" TO \"$(POSTGRES_USER)\";" \
		-c "GRANT USAGE, CREATE ON SCHEMA app TO \"$(POSTGRES_USER)\";" \
		-c "ALTER ROLE \"$(POSTGRES_USER)\" SET search_path = app, public;"

test-live-db:
	@printf '%s\n' 'Checking live PostgreSQL, app schema, and PGVector...'
	$(PSQL_SUPERUSER) \
		-v ON_ERROR_STOP=1 \
		-c "select extname from pg_extension where extname = 'vector';" \
		-c "select schema_name from information_schema.schemata where schema_name = 'app';"
	$(PSQL_APP) \
		-v ON_ERROR_STOP=1 \
		-c "create table if not exists app.live_smoke_check (id integer primary key);" \
		-c "drop table app.live_smoke_check;"

lint:
	$(RUFF) check services libs tests

typecheck:
	$(PYRIGHT)

format:
	@printf '%s\n' 'No formatter is configured yet. Future Python and frontend formatters should run here.'

migrate:
	@printf '%s\n' 'No database migrations exist yet. Local PostgreSQL bootstrap runs only on an empty data volume.'

seed:
	@printf '%s\n' 'No seed data task exists yet. Future tasks must use synthetic development data only.'
