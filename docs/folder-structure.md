# Folder Structure

This document describes the intended repository layout for GridLens. The current
repository may start with documentation only; implementation directories should
be added as the platform is built.

GridLens is designed as a production-minded, multi-tenant platform with clear
boundaries between product documentation, backend services, shared libraries,
frontend code, infrastructure, local development tooling, and operational
scripts.

## Top-Level Layout

```text
gridlens-ai-platform/
├── docs/
├── services/
├── libs/
├── frontend/
├── infra/
├── scripts/
├── tests/
├── tools/
├── .github/
├── docker-compose.yml
├── Makefile
└── README.md
```

## Directory Responsibilities

### `docs/`

Project documentation that explains what the product does, how the system is
designed, and why major decisions were made.

Expected contents:

- `requirements.md`: product requirements, personas, scope, and target system
  behavior.
- `architecture.md`: technical architecture, service boundaries, request flows,
  deployment model, and major tradeoffs.
- `local-development.md`: local Docker Compose, AWS SSO, live AWS dependency,
  debugger, and development image conventions.
- `data-model.md`: core entities, relationships, tenant-scoping rules, and data
  lineage model.
- `coding-standards.md`: project conventions for Python, TypeScript, testing,
  formatting, errors, logging, and security-sensitive code.
- `folder-structure.md`: this repository layout guide.
- `adr/`: architecture decision records for important technical choices.
- `runbooks/`: operational procedures for deployments, incidents, migrations,
  and local troubleshooting.
- `api/`: human-authored API notes or generated OpenAPI artifacts.

Documentation should be kept close to implementation changes. When a service,
data model, deployment path, or tenant-isolation assumption changes, the
corresponding document should change in the same workstream.

### `services/`

Backend service code. Each service owns a bounded area of product behavior and
should expose a narrow interface to the rest of the platform.

Recommended structure:

```text
services/
├── api-gateway/
├── identity-service/
├── dataset-catalog-service/
├── ingestion-service/
├── transformation-service/
├── evaluation-service/
├── reporting-service/
├── rag-service/
├── audit-service/
└── usage-cost-service/
```

Service responsibilities:

- `api-gateway/`: backend-for-frontend entry point, HTTP routing, request
  validation, auth enforcement, tenant context attachment, and response models.
- `identity-service/`: tenants, users, roles, invitations, tenant settings, and
  feature flags.
- `dataset-catalog-service/`: dataset metadata, schema definitions, source-file
  registration, status, and lineage records.
- `ingestion-service/`: upload registration, file inspection, validation,
  quarantine handling, and ingestion job orchestration.
- `transformation-service/`: normalization from raw inputs into curated,
  queryable, tenant-scoped tables.
- `evaluation-service/`: program evaluation configuration, baseline modeling,
  savings estimation, anomaly generation, and model-run metadata.
- `reporting-service/`: evidence packages, generated summaries, downloadable
  exports, and scheduled reports.
- `rag-service/`: document parsing, chunking, embeddings, retrieval, prompt
  orchestration, citations, refusals, and RAG evaluation.
- `audit-service/`: security, data, job, AI, and business audit events.
- `usage-cost-service/`: tenant-level usage tracking for storage, processed
  rows, jobs, API calls, LLM tokens, and estimated cost.

Each Python service should follow the same internal layering:

```text
services/<service-name>/
├── src/
│   └── gridlens_<service_name>/
│       ├── api/
│       ├── application/
│       ├── domain/
│       ├── infrastructure/
│       ├── workers/
│       ├── config.py
│       └── main.py
├── tests/
├── migrations/
├── pyproject.toml
├── Dockerfile
└── README.md
```

Layer responsibilities:

- `api/`: HTTP routes, request schemas, response schemas, dependency injection,
  and transport-specific error mapping.
- `application/`: use cases and workflows such as creating tenants, registering
  uploads, running evaluations, and generating reports.
- `domain/`: core business rules, entities, value objects, policies, and
  invariants. This layer must not depend on FastAPI, SQLAlchemy, queues, cloud
  SDKs, or vendor APIs.
- `infrastructure/`: database repositories, queue clients, object-storage
  adapters, external API clients, email providers, LLM clients, and cloud
  integrations.
- `workers/`: background job handlers for ingestion, transformation,
  evaluation, document indexing, exports, and retries.
- `tests/`: service-local unit, integration, and contract tests.
- `migrations/`: Alembic migrations or service-owned schema changes when that
  service owns database tables.

When the first implementation is a modular monolith instead of deployed
microservices, keep these same service and layer boundaries in code so the
system can be split later without rewriting the domain model.

### `libs/`

Shared code used by more than one service. Shared libraries should contain
stable, cross-cutting concerns only; service-specific business logic should stay
inside the owning service.

Recommended structure:

```text
libs/
├── auth/
├── config/
├── db/
├── events/
├── observability/
├── storage/
├── tenant-context/
├── testing/
└── contracts/
```

Common library responsibilities:

- `auth/`: JWT validation, permission helpers, role constants, and auth-related
  test utilities.
- `config/`: typed settings patterns, environment parsing, and shared config
  validation.
- `db/`: database session helpers, SQLAlchemy conventions, tenant row-level
  security helpers, and migration utilities.
- `events/`: event envelopes, queue message contracts, idempotency keys, and
  retry metadata.
- `observability/`: structured logging, trace correlation, metrics helpers, and
  redaction utilities.
- `storage/`: object-storage interfaces and local/S3-compatible adapters.
- `tenant-context/`: tenant identity propagation, request context, and
  guardrails that prevent cross-tenant access.
- `testing/`: shared fixtures, factories, fake adapters, and contract-test
  helpers.
- `contracts/`: versioned API/event/data contracts shared across services and
  workers.

Libraries should be small and intentionally versioned. Avoid turning `libs/`
into a dumping ground for convenience functions.

Current implementation notes:

- Each Python library uses `src/gridlens_<capability>/` plus a local `tests/`
  directory.
- The repo-level `Makefile` exposes the source paths through `LIB_PYTHONPATH`
  for offline `unittest` discovery until a formal Python workspace/package
  manager is introduced.
- Tenant context contracts currently live in `libs/contracts` so auth, events,
  and workers share one stable request-context shape.
- AWS, Cognito, Bedrock, and PostgreSQL-specific behavior must stay behind
  injectable seams or explicit live/local-db targets. Default library tests use
  fake adapters and synthetic tenant data only.
- Shared libraries must not import `services/`, `workers/`, frontend modules, or
  product workflow packages for dataset ingestion, evaluation, reporting, or
  assistant behavior.

### `frontend/`

React and TypeScript web application for dashboards, tenant workflows,
administration, data operations, reporting, and chat.

Recommended structure:

```text
frontend/
├── src/
│   ├── app/
│   ├── pages/
│   ├── features/
│   ├── components/
│   ├── api/
│   ├── routes/
│   ├── hooks/
│   ├── styles/
│   ├── test/
│   └── main.tsx
├── public/
├── package.json
├── vite.config.ts
└── README.md
```

Frontend responsibilities:

- `app/`: application shell, providers, layout, auth bootstrapping, and global
  state boundaries.
- `pages/`: route-level pages such as dashboard, datasets, evaluations,
  reports, chat, admin, and audit.
- `features/`: product-specific modules with local components, hooks, schemas,
  and service calls.
- `components/`: reusable UI primitives and shared layout components.
- `api/`: generated or hand-written API clients, request helpers, and error
  normalization.
- `routes/`: route definitions, protected-route behavior, and tenant-aware
  navigation.
- `hooks/`: shared React hooks that are not tied to one feature.
- `styles/`: global CSS, design tokens, Tailwind configuration, or theme files.
- `test/`: frontend test setup, factories, and rendering utilities.

Feature folders should own their UI and behavior where possible. Shared
components should be promoted only when reuse is real.

### `infra/`

Infrastructure-as-code and deployment definitions for local, staging, and
production-like environments.

Recommended structure:

```text
infra/
├── terraform/ or cdk/
├── docker/
├── environments/
│   ├── local/
│   ├── staging/
│   └── prod/
└── README.md
```

Infrastructure responsibilities:

- Cloud networking, compute, databases, object storage, queues, secrets,
  authentication, observability, and IAM.
- Environment-specific configuration and deployment parameters.
- Local development support that uses Docker Compose for services, workers, and
  PostgreSQL, with AWS SSO-backed access to development Cognito, S3, SQS, and
  Bedrock resources.
- Least-privilege IAM policies and tenant-safe resource boundaries.

Infrastructure code should not contain application secrets. Use documented
environment variables, local `.env` files for development, and managed secret
stores for deployed environments.

### `scripts/`

Operational and developer automation. Scripts should be safe, documented, and
idempotent where practical.

Expected contents:

- Database setup and migration helpers.
- Local seed-data generation.
- Synthetic data creation for demos and tests.
- One-off maintenance utilities.
- CI helper scripts.
- Deployment wrappers that call the canonical IaC tooling.

Scripts should be named by action and target, for example
`seed-local-data.sh`, `generate-synthetic-meter-data.py`, or
`migrate-local-db.sh`.

### `tests/`

Repository-level tests that cross service boundaries. Service-specific tests
belong inside each service directory.

Expected contents:

- End-to-end API workflow tests.
- Cross-service contract tests.
- Tenant-isolation regression tests.
- RAG evaluation fixtures and expected-answer datasets.
- Deployment smoke tests.

Use this directory for behavior that cannot be tested cleanly inside one
service.

### `tools/`

Developer tooling that supports the repository but is not part of runtime
application code.

Expected contents:

- Code generators.
- Schema or OpenAPI generation utilities.
- Repository maintenance scripts.
- Static analysis wrappers.
- Data-contract validation tools.

If a tool becomes part of production behavior, move it into the owning service
or library.

### `.github/`

GitHub-specific automation.

Expected contents:

- `workflows/`: CI, tests, security checks, image builds, and deployment gates.
- `pull_request_template.md`: checklist for tests, docs, migrations, and
  security considerations.
- `ISSUE_TEMPLATE/`: templates for bugs, features, architecture work, and
  documentation tasks.

CI should run formatting, linting, tests, type checks, security checks, and
build validation appropriate to the changed areas.

### Root Files

Expected root-level files:

- `README.md`: project overview, local setup, common commands, and links to key
  docs.
- `Makefile`: stable developer commands such as setup, test, lint, format,
  migrate, seed, and run.
- `docker-compose.yml`: local development dependencies and service orchestration.
- `docker-compose.dev.yml`: development overlay for hot reload, debug ports,
  bind mounts, and Dockerfile `dev` stages.
- `.env.example`: documented local environment variables without secrets.
- `.gitignore`: ignored local artifacts, caches, build outputs, and secret
  files.
- `.editorconfig`: baseline editor behavior across languages.
- `pyproject.toml`: optional root Python tooling configuration if using a
  monorepo-wide toolchain.
- `package.json`: optional root JavaScript tooling configuration if using
  workspace-level frontend tooling.

## Naming Conventions

- Use lowercase kebab-case for directories that represent deployable services,
  such as `ingestion-service`.
- Use lowercase kebab-case for documentation and scripts.
- Use Python package names with underscores, such as
  `gridlens_ingestion_service`.
- Keep generated files in clearly named generated directories or document how
  they are produced.
- Prefer explicit names over vague names such as `common`, `misc`, `utils`, or
  `helpers`.

## Ownership Rules

- A service owns its domain model, application workflows, database migrations,
  and worker logic.
- Shared libraries own reusable technical capabilities, not product-specific
  workflows.
- The frontend owns browser-facing workflows and UI state, but backend services
  remain the source of truth for authorization and tenant isolation.
- Infrastructure owns cloud resources and deployment wiring, not application
  business rules.
- Documentation owns product and architectural intent and should be updated with
  behavior-changing code.

## Tenant-Isolation Placement

Tenant isolation is a cross-cutting requirement and should appear in multiple
places:

- API request handling attaches authenticated tenant context.
- Application services pass tenant context explicitly into use cases.
- Domain policies validate tenant-scoped operations.
- Repositories enforce tenant filters and row-level security where supported.
- Object-storage keys include tenant-safe partitioning.
- Queue messages include tenant and correlation metadata.
- RAG retrieval filters by tenant, indexing readiness, and document
  deprecation state.
- Audit logs record tenant, actor, action, resource, and result.
- Tests include cross-tenant denial cases for APIs, jobs, storage, vector
  search, reports, and exports.

Do not rely on frontend filtering for tenant isolation.

## When to Add a New Folder

Add a new top-level folder only when it represents a durable repository concern.
Prefer extending an existing service, library, or documentation area first.

Good reasons to add a folder:

- A new deployable service is introduced.
- A reusable library has at least two real consumers.
- Infrastructure for a new environment or provider is added.
- Cross-service tests need shared fixtures or orchestration.
- A new documentation category has multiple documents.

Weak reasons to add a folder:

- Temporary experiments.
- One-off scripts that belong under `scripts/`.
- Unclear shared code that should remain in the owning service.
- Generated artifacts that can be recreated during build or CI.

## Current Repository Status

At the time this document was written, the repository contains the `docs/`
directory and hidden project metadata. The remaining directories above describe
the target structure for the implementation phase.
