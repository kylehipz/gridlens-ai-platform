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
- `make test-backend`: run Python service tests.
- `make test-frontend`: run frontend tests.
- `make test-local-db`: run local PostgreSQL, app schema, and PGVector smoke
  checks against an already-running Compose database.
- `make test-contracts`: run cross-service contract tests when introduced.

Cognito, S3, SQS, and Bedrock tests are intentionally not part of the default
suite in the local runtime checkpoint. Future live AWS tests must be isolated
behind an explicit target and use synthetic development data only.
