# Architecture

This document describes the high-level GridLens architecture, the main service
boundaries, and the workflow diagrams that should exist as the product design
becomes more detailed.

GridLens is a multi-tenant utility intelligence platform. The architecture is
intended to make tenant isolation, traceability, asynchronous processing, and
evidence-grounded AI behavior explicit instead of treating them as incidental
implementation details.

## Diagram Strategy

The first architecture diagram is a high-level component and dependency diagram.
It is not intended to show exact request routing inside each layer. Detailed
request, event, and data flows should be captured in separate diagrams so the
component map remains readable for onboarding.

Use these conventions across architecture diagrams:

* Layer boxes show logical grouping, not necessarily exact network boundaries.
* Solid arrows show synchronous requests, direct dependencies, or primary data
  access.
* Dashed arrows show asynchronous messaging or background processing.
* Arrow labels should describe relationship type, not endpoint-level detail.
* Tenant context, authorization checks, audit-relevant side effects, and
  correlation IDs should be shown when they materially affect the workflow.

## High-Level Component and Dependency Diagram

The diagram below shows the major logical layers, cloud services, application
services, workers, and primary dependency directions. It is meant to onboard a
reader to what exists in the system and how the pieces relate at a high level.
Detailed request paths and event sequences should be covered by the flow
diagrams listed later in this document.

<img width="1521" height="1093" alt="GridLens high-level component and dependency diagram" src="https://github.com/user-attachments/assets/3ad0fa2d-d7cf-4af0-8f7a-87b04a225d33" />

## High-Level Components

### User and Frontend

Users interact with GridLens through a React frontend delivered from S3 through
the edge layer. The frontend is responsible for user experience, navigation,
client-side state, and calling tenant-scoped APIs, but it is not the source of
truth for authorization or tenant isolation.

### DNS, CDN, and Edge Layer

The edge layer groups the externally visible entry points and frontend delivery
components:

* Route53 provides DNS.
* CloudFront serves the static frontend from S3 and can apply edge caching.
* WAF applies coarse request protection.
* The Application Load Balancer routes API traffic to backend services.
* S3 stores the frontend build artifacts.

This layer is grouped for readability. Exact frontend and API routing paths
should be shown in request-flow diagrams when needed.

### Auth Services and Integration

Cognito provides managed identity capabilities such as sign-in, token issuance,
and identity-provider integration.

Shared auth middleware and libraries are used by backend services to validate
JWTs, read Cognito JWKS, attach authenticated user context, and enforce common
permission checks. Application services still own product-specific checks such
as tenant membership, role permissions, and resource-level authorization.

### Compute Layer: APIs

API services expose tenant-scoped product behavior to the frontend and other
authorized callers. Services are grouped by product ownership rather than by AWS
resource type.

The API layer is responsible for:

* validating requests and tenant context;
* enforcing product authorization;
* coordinating application workflows;
* reading and writing service-owned data;
* enqueueing background work when processing is long-running;
* returning user-facing status resources instead of exposing infrastructure
  internals.

### Compute Layer: Workers

Workers handle long-running or retryable work such as dataset ingestion,
document chunking, embedding generation, report generation, and later program
evaluation execution. Workers consume messages from SQS and update service-owned
state in Aurora and S3.

Workers belong to the service that owns the workflow and data they mutate. API
processes and worker processes may be deployed separately, but they share the
same domain rules, event contracts, and persistence boundary.

### Messaging Layer

SQS decouples user-facing APIs from asynchronous processing. API services should
enqueue durable, tenant-scoped job messages. Worker handlers should be
idempotent where practical and should record job status, attempts, failure
reasons, and correlation metadata.

### Data Layer

Aurora PostgreSQL stores tenant-scoped application data, workflow state,
lineage, metadata, and vector-search data through PGVector.

S3 object storage stores raw uploads, generated artifacts, intermediate files,
and other large objects. S3 keys and metadata should include tenant-safe
partitioning so object access can be authorized server-side.

### AI Layer

Bedrock is a first-class dependency for AI workloads:

* embeddings for assistant document chunks and other retrievable evidence;
* LLM calls for grounded assistant responses, refusals, summaries, and
  later AI-assisted report drafting.

AI requests must be tenant-scoped, grounded in indexed evidence, observable for
usage and latency, and designed to avoid cross-tenant retrieval or citation.

## Local Development Architecture

Local development should use Docker Compose for the application services,
background workers, PostgreSQL, and developer support services. Managed AWS
dependencies should be exercised directly against development AWS resources for
Cognito, S3, SQS, and Bedrock so authentication, object storage, queueing, and
AI behavior remain close to deployed behavior.

Developer AWS access should use AWS SSO profiles. Containers should mount the
host `$HOME/.aws` directory read-only, receive `AWS_PROFILE`, `AWS_REGION`, and
`AWS_SDK_LOAD_CONFIG=1`, and rely on expiring SSO credentials instead of static
access keys.

Local observability runs through Prometheus, Loki, Tempo, Grafana, and an OTLP
collector defined under `infra/local/observability/`. Production observability
uses the same application helper calls with exporter configuration pointed at
CloudWatch metrics, CloudWatch Logs, and X-Ray, as documented in
`docs/production-observability.md`.

Each deployable service should provide a Dockerfile `dev` stage that installs
development dependencies and debugger tooling. Development-only runtime behavior
such as hot reload, bind mounts, and published debugger ports should be defined
in `docker-compose.dev.yml` as an overlay on top of the baseline
`docker-compose.yml`.

See `docs/local-development.md` for the local setup conventions.

## Service Ownership

Each service owns a bounded product area. A service may expose HTTP APIs and own
background workers. When the first implementation is a modular monolith, these
boundaries should still be preserved in modules, domain rules, tests, and data
access patterns.

### Identity and Tenant

Owns tenant onboarding, users, invitations, tenant memberships, roles, tenant
settings, enabled modules, tenant lifecycle, and tenant-level access decisions.

This service is the system of record for who can operate in a tenant workspace.
It should not rely on frontend filtering to enforce tenant access.

### Data Operations

Owns file registration, dataset catalog records, ingestion
jobs, validation, quality reports, billing data, rate data, and normalized
operational data such as properties, accounts, meters, readings, weather,
programs, and participants.

This service is the main producer of clean, traceable inputs for downstream
evaluation, dashboards, reports, and assistant context.

### Assistant

Owns assistant source documents, deprecation state, document parsing, chunking,
embeddings, retrieval, chat sessions, citations, refusals, assistant
interactions, user feedback, and assistant evaluation cases.

The assistant should treat indexed tenant evidence as the grounding source. It
should not answer from non-indexed documents, deprecated documents, another
tenant's data, or unsupported assumptions.

### Program Evaluation

Owns evaluation configuration, evaluation runs, input readiness checks,
assumptions, baseline modeling, savings estimates, model outputs, evaluation
lineage, limitations, and evaluation-linked anomalies.

This boundary is important, but detailed program evaluation flows are deferred
until the functional design is clearer.

### Insights and Reporting

Owns dashboards, evidence views, report definitions, report runs, exports,
evidence packages, and downloadable generated artifacts.

Dashboards should expose metrics with links back to evaluation runs, source
datasets, quality reports, assumptions, and limitations where available.
Evidence export and report generation flows are deferred until the business
requirements are more specific.

### Governance

Owns audit logs, usage metrics, cost rollups, AI usage summaries, platform-safe
operational views, and tenant-safe administrative visibility.

Governance behavior is cross-cutting. Product workflows should emit
audit-relevant events, but the detailed event propagation diagram is deferred
until the audit and governance requirements are more concrete.

### Alerts and Anomalies

Owns alert rules, alert events, anomaly review, anomaly resolution, and
notification-oriented workflows.

This boundary may start inside Data Operations or Program Evaluation and split
later if alerting behavior becomes large enough.

## Worker Ownership

Workers should be named and owned by the workflow they execute:

* Data Operations workers process dataset files, validate records, transform
  supported dataset types into normalized tenant-scoped tables, and generate
  quality reports.
* Assistant workers parse assistant documents, create chunks, generate
  embeddings, rebuild indexes, and run assistant evaluation cases.
* Program Evaluation workers run long-running evaluations, compute results, and
  generate evaluation-linked anomalies.
* Insights and Reporting workers generate reports, evidence packages, exports,
  and downloadable artifacts.

Worker messages should include tenant ID, actor or system identity, correlation
ID, source resource IDs, attempt metadata, and enough information to resume or
retry safely without trusting client-provided state.

## Detailed Flow Diagrams

The following flow diagrams should be designed next because they describe the
core workflows currently understood well enough to make useful implementation
decisions.

### Tenant Onboarding

Shows how a platform administrator creates a tenant, configures enabled modules
and settings, invites initial users, assigns roles, and establishes tenant-safe
workspace access.

This flow should make explicit where Cognito identity, GridLens membership,
tenant context, role authorization, and audit-relevant side effects interact.

### Dataset Ingestion

Dataset ingestion lets a tenant member upload a dataset directly to tenant-scoped
S3 object storage while the DataOps service records dataset metadata and an
ingestion job in Aurora. S3 object creation events enqueue asynchronous work for
the DataOps worker, which reads the raw object, validates and transforms the
file, writes normalized records, and updates user-visible job status.

#### High-level diagram
<img width="801" height="479" alt="image" src="https://github.com/user-attachments/assets/9db0e635-35b2-4f94-b12f-b7c625374130" />

#### Sequence diagram
<img width="3064" height="2542" alt="image" src="https://github.com/user-attachments/assets/c9318f8c-d197-4273-ba3e-d31b4267f786" />

The diagrams focus on the primary happy path. The following requirements should
be implemented and tested as part of the ingestion workflow without adding
additional clutter to the diagrams:

* Upload intents create the dataset record and pending ingestion job before
  returning a pre-signed S3 URL.
* Pre-signed URLs are scoped to tenant-safe object keys, expected content type,
  maximum upload size, checksum requirements, encryption settings, and short
  expiry windows.
* S3 and SQS delivery are treated as at-least-once. Workers should claim jobs
  with idempotent state transitions keyed by tenant ID, dataset ID, upload ID,
  object key, and object version or ETag.
* Pending uploads should expire if no matching object is uploaded within the
  allowed window.
* Workers validate file size, checksum, schema, tenant ownership, malformed
  rows, timestamp and unit conventions, and duplicate data before writing
  processed records.
* Job status should be tracked through states such as `pending_upload`,
  `processing`, `completed`, `expired`, `failed_validation`, and
  `failed_processing`.
* Worker failures should preserve enough failure reason, attempt, correlation,
  and lineage metadata to trace each raw file to the resulting dataset records
  or terminal failure state.
* Dataset DLQ messages should be monitored, alarmed, inspected, and replayed
  through an explicit remediation process after the underlying issue is fixed.

### Assistant Ingestion

Shows how assistant source material enters the system: upload, document
registration, parsing, chunking, embedding generation, vector storage,
indexing status, and document deprecation or reindexing.

This flow should distinguish document storage from dataset ingestion because
assistant context has different citation and prompt-injection risks.

### Assistant Chat

Shows how a user message becomes a grounded answer or refusal: session lookup,
authorization, tenant-scoped retrieval, indexed-source filtering, prompt
assembly, Bedrock call, citation attachment, response persistence, usage
metadata, and user-facing answer.

This flow should explicitly show refusal behavior when evidence is missing,
retrieval returns non-indexed or deprecated context, or the user asks for
unauthorized data.

## Deferred Flow Diagrams

The following flows are intentionally deferred. They are important, but they
need more functional design before detailed architecture diagrams will be
useful.

* Program evaluation execution: evaluation setup, input readiness, assumptions,
  model execution, savings estimates, limitations, and evaluation lineage.
* Evidence export and reporting: evaluation summary reports, evidence packages,
  machine-readable exports, report versions, and generated artifact storage.
* Audit and governance event propagation: where product workflows emit audit
  events, how governance data is stored, and how tenant-safe operational views
  are built.

Current diagrams should still leave clear hooks for these future flows. For
example, dataset ingestion should produce datasets, quality reports, and
lineage records that program evaluation and reporting can consume later.

## Cross-Cutting Requirements

### Tenant Isolation

Tenant isolation must be enforced server-side. API handlers, application use
cases, repositories, object-storage adapters, queue messages, vector retrieval,
reports, and worker jobs should all carry explicit tenant context.

Every tenant-owned read or write should be scoped by tenant and should fail
safely when tenant context is missing or unauthorized.

### Authorization

Frontend navigation can hide unavailable actions, but backend services must
enforce role and permission checks. Authorization decisions should be explicit
near workflow entry points and should be tested for cross-tenant denial cases.

### Traceability

Important outputs should link back to their source inputs and workflow state.
At minimum, datasets, quality reports, assistant answers, evaluation
runs, dashboards, and generated artifacts should preserve enough metadata to
explain how they were produced.

### Observability and Operations

User-facing workflows should expose stable status resources for long-running
work. Operational metadata should include request IDs, correlation IDs, job
attempts, failure reasons, timing, and safe usage indicators.

Logs and metrics should be useful for troubleshooting without exposing secrets,
raw tokens, full prompts, or tenant data beyond the permissions of the viewer.
