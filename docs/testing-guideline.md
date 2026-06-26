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

No test command is checked in yet. When tooling is added, expose stable commands
through `Makefile`, for example:

- `make test`: run the full test suite.
- `make test-backend`: run Python service tests.
- `make test-frontend`: run frontend tests.
- `make test-contracts`: run cross-service contract tests.
