# GridLens AI Platform

GridLens is a multi-tenant utility intelligence, program evaluation, and
AI decision-support platform. It is designed to help utilities, municipalities,
building operators, and program teams ingest operational data, validate quality,
run transparent evaluations, ask grounded questions, and export evidence-backed
reports.

## Repository Status

This repository is currently in the foundation stage. It contains product and
architecture documentation plus contributor scaffolding. Implementation
directories such as `services/`, `libs/`, `frontend/`, `infra/`, `scripts/`,
and `tests/` are planned and should be added as the corresponding work begins.

Use the root commands in this README as the stable contributor entry point. They
currently provide lightweight checks for the documentation-first repository and
can be expanded behind the same target names as source code lands.

## Quick Start

```sh
make setup
make test
```

`make setup` prints the current setup guidance and verifies that the repository
has the expected baseline files. `make test` succeeds in the current docs-only
state and delegates to backend and frontend placeholder targets until those
subsystems exist.

For local configuration, copy or inspect `.env.example` before running future
services. It contains public-safe placeholders only.

## Commands

| Command | Purpose |
|---|---|
| `make setup` | Verify baseline files and print setup guidance. |
| `make test` | Run the available repository test targets. |
| `make test-backend` | Run backend tests when `services/` exists; placeholder today. |
| `make test-frontend` | Run frontend tests when `frontend/` exists; placeholder today. |
| `make lint` | Check repository hygiene such as conflict markers and whitespace, including committed PR diff whitespace in CI. |
| `make format` | Placeholder for future formatters. |
| `make migrate` | Placeholder for future database migrations. |
| `make seed` | Placeholder for future synthetic development seed data. |
| `make run` | Placeholder for the future local application stack. |

## Documentation Map

- [Product requirements](docs/requirements.md): product scope, personas,
  principles, functional requirements, and backlog direction.
- [Architecture](docs/architecture.md): component boundaries, dependency model,
  deployment posture, and current data-flow diagrams.
- API documentation: planned under `docs/api/` when endpoint contracts are
  introduced.
- [Data model](docs/data-model.md): core entities, tenant-scoping rules, and
  lineage concepts.
- [Local development](docs/local-development.md): intended Docker Compose and
  AWS development posture.
- [Folder structure](docs/folder-structure.md): target repository layout and
  ownership rules.
- [Testing guideline](docs/testing-guideline.md): test strategy, locations,
  naming, and tenant-isolation expectations.
- [Pull request guideline](docs/pr-guideline.md): commit, PR, review, and
  documentation expectations.
- [Coding standards](docs/coding-standards.md): backend, frontend, testing,
  security, observability, and AI/RAG implementation conventions.

## Contributor Notes

- Do not commit secrets, credentials, real customer data, or regulated data.
- Use synthetic data for local development and tests.
- Enforce tenant isolation server-side for APIs, workers, storage, retrieval,
  logs, reports, and exports.
- Update documentation when behavior, architecture, commands, or conventions
  change.
