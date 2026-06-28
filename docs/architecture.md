# Microservice Design

This document defines the high-level service ownership boundaries for GridLens.
Detailed request flows, event flows, deployment diagrams, and data ownership
diagrams will be designed separately.

## Gateway

GridLens may use Kong, Envoy, or a similar edge gateway for routing, TLS,
rate-limiting, request IDs, and coarse-grained gateway policy.

Application services still own product-specific authorization, tenant membership
checks, role and permission enforcement, audit emission, and response behavior.

## Service Ownership

Each service may contain both HTTP APIs and background workers. API and worker
processes can be deployed separately, but they share the same service ownership,
domain rules, data contracts, and persistence boundary.

## Services

* Identity and Tenant - tenant onboarding, users, invitations, tenant
  memberships, roles, tenant settings, and tenant lifecycle.
* Data Operations - file registration, dataset catalog, dataset versions,
  ingestion jobs, validation, quality reports, billing data, rate data, and
  normalized operational data such as properties, accounts, meters, readings,
  weather, programs, and participants.
* Assistant - assistant source documents, approval workflow, document parsing,
  chunking, embeddings, chat sessions, retrieval, citations, refusals, assistant
  interactions, and assistant evaluation.
* Program Evaluation - evaluation configuration, evaluation runs, input
  readiness checks, assumptions, baseline modeling, savings estimates, model
  outputs, evaluation lineage, and evaluation-linked anomalies.
* Insights and Reporting - dashboards, evidence views, report definitions,
  report runs, exports, evidence packages, and downloadable generated artifacts.
* Governance - audit logs, usage metrics, cost rollups, AI usage summaries,
  platform-safe operational views, and tenant-safe administrative visibility.
* Alerts and Anomalies - alert rules, alert events, anomaly review, anomaly
  resolution, and notification-oriented workflows. This boundary may start
  inside Data Operations or Program Evaluation and split later if alerting
  behavior becomes large enough.

## Worker Ownership

Workers belong to the service that owns the workflow and data they mutate.

* Data Operations workers process dataset files, validate records, transform
  supported dataset types into normalized tenant-scoped tables, and generate
  quality reports.
* Assistant workers parse assistant documents, create chunks, generate
  embeddings, rebuild indexes, and run assistant evaluation cases.
* Program Evaluation workers run long-running evaluations, compute results, and
  generate evaluation-linked anomalies.
* Insights and Reporting workers generate reports, evidence packages, exports,
  and downloadable artifacts.
