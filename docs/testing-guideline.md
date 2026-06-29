# Testing Guideline

## Testing Strategy

Testing frameworks are not configured yet. As implementation begins, use tests to
protect service boundaries, tenant isolation, data correctness, and user-facing
workflows.

Recommended defaults:

- Python services: `pytest`.
- Frontend: Vitest and React Testing Library.
- Cross-service workflows: repository-level tests under `tests/`.
- RAG behavior: fixture-based evaluation cases with expected evidence and
  refusal outcomes.

## Test Locations

Place service-specific tests inside the owning service:

```text
services/<service-name>/tests/
```

Use repo-level `tests/` only for behavior that crosses service boundaries, such
as API workflows, event contracts, tenant-isolation regressions, and deployment
smoke tests.

## Naming Conventions

Use predictable names:

- Python test files: `test_*.py`.
- Frontend test files: `*.test.ts` or `*.test.tsx`.
- Fixtures: name by domain and purpose, such as `tenant_a_dataset.json`.

Test names should describe behavior, not implementation details. Prefer
`test_denies_cross_tenant_dataset_access` over `test_filter_called`.

## Tenant-Isolation Requirements

Every tenant-scoped feature should include denial tests for cross-tenant access.
Cover APIs, background jobs, object storage paths, vector retrieval, reports,
exports, and audit events where relevant.

## Command Conventions

Expose stable commands through `Makefile`:

- `make test`: run the default offline suite without AWS credentials, network
  access, or an active AWS SSO session.
- `make test-backend`: run all configured Python tests with pytest from the
  repo-local `.venv`.
- `make test-frontend`: run frontend tests.
- `make test-contracts`: run shared role, status, envelope, pagination, tenant
  context, audit, event, and drift tests.
- `make test-libs`: run all shared library unit tests, including fake storage
  and AI adapters, auth/config/db/events/observability helpers, and
  import-boundary guards.
- `make test-local-db`: run local PostgreSQL, app schema, and PGVector smoke
  checks against an already-running Compose database.
- `make bootstrap-live-db`: initialize a live PostgreSQL database with the app
  role, app schema, and PGVector extension.
- `make test-live-db`: run PostgreSQL, app schema, and PGVector smoke checks
  against a database reachable through `POSTGRES_HOST` and `POSTGRES_PORT`, or
  through `POSTGRES_CONTAINER_ID`.

Cognito, S3, SQS, and Bedrock tests are intentionally not part of the default
suite. Live AWS tests must be isolated behind an explicit target and use
synthetic development data only.

CI runs `make typecheck`, `make lint`, `make test`, `make bootstrap-live-db`,
and `make test-live-db`. Database checks use a PostgreSQL/PGVector service
container. AWS-facing configuration in CI must use mock values and must not
require real AWS credentials, SSO, or network access to managed AWS services.

`pyproject.toml` is the source of truth for pytest discovery paths and source
import paths. Add new Python test roots there instead of appending more
`unittest discover` commands to the Makefile.

Ruff is the backend Python linter. `make lint` runs `ruff check` using the
configuration in `pyproject.toml`, then runs repository hygiene checks for merge
conflict markers, accidental AWS credentials, and whitespace.
