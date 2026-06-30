# Coding Standards

GridLens is a production-minded, multi-tenant data and AI platform. These
standards define the initial conventions for implementation work. They should
evolve with the codebase, but changes to conventions should be explicit and
documented.

## General Principles

- Keep tenant isolation, auditability, and explainability visible in code
  reviews.
- Prefer small modules with clear ownership over shared convenience code.
- Keep source examples, fixtures, and demos public-safe by using synthetic data.
- Expose stable contributor commands through the root `Makefile`.
- Update relevant documentation when behavior, commands, architecture, or
  conventions change.

## Python Backend

Python services should follow the service layout described in
`docs/folder-structure.md`:

- `api/`: transport concerns, request and response schemas, dependency wiring,
  and HTTP error mapping.
- `application/`: use cases, workflows, transaction boundaries, authorization
  decisions, and orchestration.
- `domain/`: business rules, entities, value objects, and invariants. Domain
  code must not depend on FastAPI, SQLAlchemy, queues, object storage, cloud
  SDKs, or LLM vendors.
- `infrastructure/`: repositories, external clients, queue adapters, storage
  adapters, auth providers, and observability integrations.
- `workers/`: background handlers for ingestion, transformation, evaluation,
  indexing, reporting, retries, and dead-letter workflows.

Use typed function signatures for public module boundaries. Prefer explicit
data objects or schema models over passing unstructured dictionaries through
multiple layers. Keep side effects at the edges and make domain logic easy to
unit test.

## TypeScript and React

Frontend code should be written in TypeScript and organized by application
shell, pages, features, shared components, API clients, hooks, styles, and test
utilities.

- Keep route-level data loading and authorization state explicit.
- Keep feature-specific components inside the owning feature until they are
  reused by multiple areas.
- Use typed API clients and response schemas when backend contracts exist.
- Treat tenant context as application state that comes from authenticated
  server responses, not as a client-side filter that grants access.
- Keep forms accessible, validate user input before submission, and preserve
  server-side validation as the source of truth.

## Testing

Use tests to protect behavior that is hard to inspect manually:

- Python services: `pytest`.
- Frontend: Vitest and React Testing Library.
- Cross-service behavior: repository-level tests under `tests/`.
- RAG behavior: fixture-based evaluation cases covering evidence, citations,
  ambiguity, and refusal behavior.

Tenant-scoped features must include denial tests for cross-tenant access. Cover
API reads and writes, background jobs, object storage keys, vector retrieval,
reports, exports, logs, and audit records where relevant.

Unit tests should run without network access or AWS credentials. Live AWS tests
must be explicit, opt-in, synthetic-data-only, and isolated to development
resources.

## Security and Tenant Isolation

Tenant isolation must be enforced server-side. Frontend filtering is useful for
presentation only and must not be treated as an authorization boundary.

- Attach tenant context at authenticated request boundaries.
- Check tenant authorization in application use cases before accessing
  tenant-scoped data.
- Include tenant identifiers in database predicates, object storage paths,
  queue messages, vector metadata, reports, exports, and audit events.
- Avoid cross-tenant batch operations unless they are platform-admin workflows
  with explicit authorization and audit records.
- Do not log credentials, tokens, signed URLs, prompts, retrieved context,
  regulated data, or customer-like payloads.
- Keep secrets in environment or managed secret stores, never in source,
  documentation examples, fixtures, images, or generated artifacts.

Development authentication flags such as `DEV_AUTH_ENABLED` are local-only
shortcuts. They must not bypass server-side tenant checks or appear in
production deployment paths.

## Authentication and Authorization

Authentication code should verify identity, attach a tenant-aware principal, and
make authorization decisions explicit. Role and permission checks should live in
shared auth or application policy helpers rather than being duplicated in route
handlers.

Every privileged action should make the actor, tenant, target resource, and
decision reason available for audit logging. Authorization failures should be
clear to clients without leaking whether another tenant's resource exists.

## Database and Migrations

Database changes should be made through migrations once persistence exists.
Migrations must be deterministic, reviewable, and paired with tests or manual
verification notes.

- Include tenant-scoping columns on tenant-owned tables.
- Prefer foreign keys and constraints for important invariants.
- Keep data migrations idempotent where practical.
- Document backfills, destructive changes, and rollback constraints in pull
  requests.
- Never use production or customer data in local seeds or tests.

## Errors and API Responses

Return errors that help users recover without exposing sensitive details.

- Map validation, authorization, not-found, conflict, rate-limit, and internal
  failures to distinct response shapes or status codes.
- Do not leak stack traces, credentials, prompts, retrieved chunks, SQL, or
  tenant identifiers from other tenants.
- Preserve internal correlation IDs so operators can connect user-visible
  errors to logs and traces.

## Logging and Observability

Use structured logs and include request, tenant, job, trace, and correlation
identifiers where available. Logs should support incident review, audit
investigation, and cost analysis without exposing sensitive payloads.

Metrics and traces should track service health, queue depth, job duration,
validation failures, evaluation runs, retrieval quality signals, export
activity, and AI usage or cost drivers. Redact sensitive values before logs,
metrics, traces, or exceptions leave the service boundary.

Backend services and workers should call `gridlens_observability` helpers rather
than backend-specific telemetry SDKs directly. Required signal fields, standard
metric names, span naming, local exporter settings, production exporter
settings, and redaction rules are maintained in `libs/observability/README.md`.

## AI and RAG Safety

AI features are governed product behavior, not generic chat. Retrieval,
prompting, response generation, and evaluation must preserve tenant boundaries.

- Retrieve only tenant-authorized context.
- Store tenant and source metadata with chunks, embeddings, prompts, responses,
  citations, and evaluation artifacts.
- Require citations for factual answers grounded in indexed evidence.
- Refuse or ask for clarification when evidence is missing, ambiguous, or
  outside the user's tenant scope.
- Avoid unsupported numeric claims, policy claims, or operational
  recommendations.
- Test refusal behavior, citation accuracy, prompt-injection resistance, and
  cross-tenant retrieval denial.

Prompts, retrieved context, and model responses are tenant-scoped data. Treat
them with the same care as source documents, reports, and audit events.
