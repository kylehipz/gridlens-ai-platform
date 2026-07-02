# API Endpoints

**Document purpose:** Define the initial GridLens HTTP API surface at the
endpoint, behavior, and authorization level.

This document intentionally does not define request schemas, response schemas,
database fields, or OpenAPI details. It describes what each endpoint does and
which role or permission should authorize it so the backend, frontend, and tests
can align before implementation.

## API Conventions

- Base path: `/api/v1`.
- Tenant-owned product resources are scoped under `/tenants/{tenant_id}` unless
  the endpoint is platform-wide.
- The authenticated user and active tenant context must be enforced
  server-side.
- Mutating endpoints should create audit events when they affect tenant access,
  uploaded data, evaluations, assistant context, reports, exports, or settings.
- Long-running work should return a tracked resource, job, run, or export that
  can be polled for status.
- File download endpoints return a generated or stored artifact only after
  authorization and tenant-scope checks.

## Authorization Model

The `Access` column lists the minimum role or permission expected for the
endpoint. Exact role names can change during implementation, but the permission
boundary should stay stable.

Tenant roles:

- `Tenant Admin`: can manage tenant settings, members, assistant documents,
  audit views, and tenant-scoped configuration.
- `Analyst`: can upload datasets, run processing workflows, create evaluations,
  inspect data quality, and generate analytical outputs.
- `Program Manager`: can view dashboards, evaluations, reports, and ask
  assistant questions.
- `Auditor`: can review lineage, evidence packages, report outputs, and audit
  activity.
- `Viewer`: can read tenant resources permitted by role but cannot mutate product state.

Platform roles:

- `Platform Admin`: can create and manage tenants and inspect platform-wide
  administrative data.
- `Platform Operator`: can inspect platform health, jobs, and cross-tenant
  operational rollups without accessing tenant-owned source data unless also
  authorized for that tenant.

Cognito JWTs authenticate identity only. Platform roles and tenant roles are
resolved from GridLens data, not from JWT authorization claims.

Permission shorthand:

- `Any tenant member`: any active membership in the target tenant.
- `Self`: the authenticated user's own account context.
- `System`: internal service or worker identity, not a normal browser user.
- `Owner`: the user who created the resource, unless a stronger tenant role is
  also listed.
- `Tenant Admin or Analyst` means either role is sufficient.

## Authentication and Current User

| Method | Path | Access | Purpose |
| --- | --- | --- | --- |
| `GET` | `/api/v1/me` | `Self` | Return the authenticated user's profile, active memberships, roles, and accessible tenants. |
| `GET` | `/api/v1/me/tenants` | `Self` | List tenant workspaces the authenticated user can access. |
| `POST` | `/api/v1/me/active-tenant` | `Any tenant member` | Set or validate the tenant context the frontend should use for tenant-scoped workflows. |

## Platform Tenancy

| Method | Path | Access | Purpose |
| --- | --- | --- | --- |
| `GET` | `/api/v1/tenants` | `Platform Admin` | List tenant workspaces for platform administration and support. |
| `POST` | `/api/v1/tenants` | `Platform Admin` | Create a tenant workspace and record the creation as an audit event. |
| `GET` | `/api/v1/tenants/{tenant_id}` | `Platform Admin` or `Any tenant member` | Return tenant workspace details and status. Tenant members only see their own tenant. |
| `PATCH` | `/api/v1/tenants/{tenant_id}` | `Platform Admin` | Update tenant workspace metadata, status, or high-level configuration. |
| `GET` | `/api/v1/tenants/{tenant_id}/settings` | `Tenant Admin` or `Viewer` | Return tenant preferences such as units, enabled modules, labels, and default reporting options. |
| `PATCH` | `/api/v1/tenants/{tenant_id}/settings` | `Tenant Admin` | Update tenant preferences that affect only the selected tenant. |

## Tenant Memberships and Invitations

| Method | Path | Access | Purpose |
| --- | --- | --- | --- |
| `GET` | `/api/v1/tenants/{tenant_id}/members` | `Tenant Admin` | List users and invitations for a tenant administration view. |
| `POST` | `/api/v1/tenants/{tenant_id}/invitations` | `Tenant Admin` | Invite a user to the tenant with a role and membership status. |
| `GET` | `/api/v1/tenants/{tenant_id}/invitations` | `Tenant Admin` | List pending, accepted, expired, or revoked invitations for the tenant. |
| `POST` | `/api/v1/tenants/{tenant_id}/invitations/{invitation_id}/resend` | `Tenant Admin` | Resend a tenant invitation when it is still eligible. |
| `POST` | `/api/v1/tenants/{tenant_id}/invitations/{invitation_id}/revoke` | `Tenant Admin` | Revoke a pending invitation and audit the change. |
| `PATCH` | `/api/v1/tenants/{tenant_id}/members/{membership_id}` | `Tenant Admin` | Change a member role or lifecycle status within the tenant. |
| `POST` | `/api/v1/tenants/{tenant_id}/members/{membership_id}/deactivate` | `Tenant Admin` | Deactivate a tenant member while preserving historical audit references. |

## File Objects

| Method | Path | Access | Purpose |
| --- | --- | --- | --- |
| `POST` | `/api/v1/tenants/{tenant_id}/files/upload-url` | `Tenant Admin` or `Analyst` | Create a tenant-scoped upload target for raw dataset files, assistant source documents, bills, or other supported artifacts. |
| `GET` | `/api/v1/tenants/{tenant_id}/files/{file_id}` | `Tenant Admin`, `Analyst`, or `Auditor` | Return metadata for a stored file object. |
| `GET` | `/api/v1/tenants/{tenant_id}/files/{file_id}/download-url` | `Tenant Admin`, `Analyst`, or `Auditor` | Create a short-lived authorized download URL for an uploaded or generated file. |

## Dataset Catalog

| Method | Path | Access | Purpose |
| --- | --- | --- | --- |
| `GET` | `/api/v1/tenants/{tenant_id}/datasets` | `Any tenant member` | List tenant datasets with catalog metadata, type, processing status, and latest quality status. |
| `POST` | `/api/v1/tenants/{tenant_id}/datasets` | `Analyst` | Register a dataset from an uploaded file and start the initial processing workflow when appropriate. |
| `GET` | `/api/v1/tenants/{tenant_id}/datasets/{dataset_id}` | `Any tenant member` | Return dataset details, current readiness, deprecation state, lineage summary, and related activity links. |
| `PATCH` | `/api/v1/tenants/{tenant_id}/datasets/{dataset_id}` | `Tenant Admin` or `Analyst` | Update dataset metadata such as name, description, or deprecation state. |
| `POST` | `/api/v1/tenants/{tenant_id}/datasets/{dataset_id}/deprecate` | `Tenant Admin` | Mark a dataset as deprecated so it is not selected for new evaluations by default. |
| `POST` | `/api/v1/tenants/{tenant_id}/datasets/{dataset_id}/restore` | `Tenant Admin` | Restore a deprecated dataset when an authorized user decides it may be used again. |

## Ingestion Sources and Jobs

| Method | Path | Access | Purpose |
| --- | --- | --- | --- |
| `GET` | `/api/v1/tenants/{tenant_id}/ingestion-sources` | `Tenant Admin` or `Analyst` | List reusable ingestion sources such as manual upload, scheduled import, SFTP, or provider feed definitions. |
| `POST` | `/api/v1/tenants/{tenant_id}/ingestion-sources` | `Tenant Admin` | Create an ingestion source configuration without storing secrets in the API payload. |
| `GET` | `/api/v1/tenants/{tenant_id}/ingestion-sources/{source_id}` | `Tenant Admin` or `Analyst` | Return one ingestion source and its operational status. |
| `PATCH` | `/api/v1/tenants/{tenant_id}/ingestion-sources/{source_id}` | `Tenant Admin` | Update non-secret ingestion source settings or status. |
| `GET` | `/api/v1/tenants/{tenant_id}/ingestion-jobs` | `Tenant Admin`, `Analyst`, or `Auditor` | List processing jobs with filters for status, dataset, source, date range, and failure category. |
| `GET` | `/api/v1/tenants/{tenant_id}/ingestion-jobs/{job_id}` | `Tenant Admin`, `Analyst`, or `Auditor` | Return job progress, counters, timing, failure reason, and links to related datasets or quality reports. |
| `POST` | `/api/v1/tenants/{tenant_id}/ingestion-jobs/{job_id}/retry` | `Analyst` | Retry an eligible failed job with a new attempt number and audit trail. |
| `GET` | `/api/v1/tenants/{tenant_id}/ingestion-jobs/{job_id}/errors` | `Tenant Admin`, `Analyst`, or `Auditor` | List row-level or record-level errors for a validation or ingestion job. |

## Data Quality

| Method | Path | Access | Purpose |
| --- | --- | --- | --- |
| `GET` | `/api/v1/tenants/{tenant_id}/quality-reports` | `Any tenant member` | List data-quality reports across datasets for review queues and dashboard summaries. |
| `GET` | `/api/v1/tenants/{tenant_id}/quality-reports/{report_id}` | `Any tenant member` | Return a quality report summary, severity counts, score, and issue categories. |
| `GET` | `/api/v1/tenants/{tenant_id}/quality-reports/{report_id}/issues` | `Tenant Admin`, `Analyst`, or `Auditor` | List blocking, warning, and informational quality issues from a report. |
| `GET` | `/api/v1/tenants/{tenant_id}/datasets/{dataset_id}/quality-report` | `Any tenant member` | Return the latest quality report for a dataset. |

## Utility Assets and Operational Data

These endpoints support browsing normalized data produced by ingestion. They are
read-oriented in the initial API because uploads and transformations own writes.

| Method | Path | Access | Purpose |
| --- | --- | --- | --- |
| `GET` | `/api/v1/tenants/{tenant_id}/properties` | `Any tenant member` | List tenant properties, buildings, or sites with search and filter support. |
| `GET` | `/api/v1/tenants/{tenant_id}/properties/{property_id}` | `Any tenant member` | Return a property profile and related accounts, meters, participation, anomalies, or evaluations. |
| `GET` | `/api/v1/tenants/{tenant_id}/utility-accounts` | `Tenant Admin`, `Analyst`, `Program Manager`, or `Auditor` | List utility accounts with masked identifiers and provider filters. |
| `GET` | `/api/v1/tenants/{tenant_id}/utility-accounts/{account_id}` | `Tenant Admin`, `Analyst`, `Program Manager`, or `Auditor` | Return one utility account and related meters, properties, readings, or bills. |
| `GET` | `/api/v1/tenants/{tenant_id}/meters` | `Any tenant member` | List meters with filters for property, account, service type, and status. |
| `GET` | `/api/v1/tenants/{tenant_id}/meters/{meter_id}` | `Any tenant member` | Return meter metadata and lineage details. |
| `GET` | `/api/v1/tenants/{tenant_id}/meters/{meter_id}/readings` | `Tenant Admin`, `Analyst`, `Program Manager`, or `Auditor` | Return time-series meter readings for charts, review, or evaluation investigation. |
| `GET` | `/api/v1/tenants/{tenant_id}/weather-observations` | `Any tenant member` | Return weather observations for a location group and date range. |
| `GET` | `/api/v1/utility-providers` | `Authenticated user` | List shared utility provider reference records. |

## Programs and Participants

| Method | Path | Access | Purpose |
| --- | --- | --- | --- |
| `GET` | `/api/v1/tenants/{tenant_id}/programs` | `Any tenant member` | List tenant programs available for dashboards and evaluations. |
| `POST` | `/api/v1/tenants/{tenant_id}/programs` | `Tenant Admin` or `Analyst` | Create a tenant program for participation tracking and evaluation. |
| `GET` | `/api/v1/tenants/{tenant_id}/programs/{program_id}` | `Any tenant member` | Return program details, status, participation summary, and evaluation history links. |
| `PATCH` | `/api/v1/tenants/{tenant_id}/programs/{program_id}` | `Tenant Admin` or `Analyst` | Update tenant program metadata or lifecycle status. |
| `GET` | `/api/v1/tenants/{tenant_id}/programs/{program_id}/participants` | `Tenant Admin`, `Analyst`, `Program Manager`, or `Auditor` | List program participants or participating sites/accounts. |
| `GET` | `/api/v1/tenants/{tenant_id}/programs/{program_id}/participants/{participant_id}` | `Tenant Admin`, `Analyst`, or `Auditor` | Return participant-level detail for analyst drilldown. |

## Billing and Rates

| Method | Path | Access | Purpose |
| --- | --- | --- | --- |
| `GET` | `/api/v1/tenants/{tenant_id}/billing-statements` | `Tenant Admin`, `Analyst`, or `Auditor` | List imported bill statements with filters for account, property, service type, date range, and status. |
| `GET` | `/api/v1/tenants/{tenant_id}/billing-statements/{statement_id}` | `Tenant Admin`, `Analyst`, or `Auditor` | Return one bill statement and its source-file lineage. |
| `GET` | `/api/v1/tenants/{tenant_id}/billing-statements/{statement_id}/line-items` | `Tenant Admin`, `Analyst`, or `Auditor` | Return line items for a bill statement. |
| `GET` | `/api/v1/tenants/{tenant_id}/rate-plans` | `Tenant Admin` or `Analyst` | List tenant rate plans used for cost estimates or bill explanations. |
| `POST` | `/api/v1/tenants/{tenant_id}/rate-plans` | `Tenant Admin` or `Analyst` | Create a tenant rate plan. |
| `GET` | `/api/v1/tenants/{tenant_id}/rate-plans/{rate_plan_id}` | `Tenant Admin` or `Analyst` | Return rate plan details and active components. |
| `PATCH` | `/api/v1/tenants/{tenant_id}/rate-plans/{rate_plan_id}` | `Tenant Admin` or `Analyst` | Update rate plan metadata or lifecycle status. |
| `GET` | `/api/v1/tenants/{tenant_id}/utility-accounts/{account_id}/rate-plans` | `Tenant Admin` or `Analyst` | List effective-dated rate plan assignments for an account. |
| `POST` | `/api/v1/tenants/{tenant_id}/utility-accounts/{account_id}/rate-plans` | `Tenant Admin` or `Analyst` | Assign a rate plan to an account for an effective date range. |

## Evaluations

| Method | Path | Access | Purpose |
| --- | --- | --- | --- |
| `GET` | `/api/v1/tenants/{tenant_id}/evaluations` | `Any tenant member` | List evaluation runs with filters for program, status, type, date range, and approval state. |
| `POST` | `/api/v1/tenants/{tenant_id}/evaluations` | `Analyst` | Create and start an evaluation run after validating required input readiness. |
| `GET` | `/api/v1/tenants/{tenant_id}/evaluations/{evaluation_id}` | `Any tenant member` | Return evaluation run details, status, assumptions, limitations, input lineage, and summary results. |
| `POST` | `/api/v1/tenants/{tenant_id}/evaluations/{evaluation_id}/cancel` | `Analyst` | Cancel a queued or running evaluation when cancellation is still possible. |
| `POST` | `/api/v1/tenants/{tenant_id}/evaluations/{evaluation_id}/approve` | `Tenant Admin` | Mark a completed evaluation as approved for reporting. |
| `POST` | `/api/v1/tenants/{tenant_id}/evaluations/{evaluation_id}/unapprove` | `Tenant Admin` | Remove reporting approval from an evaluation when permitted. |
| `GET` | `/api/v1/tenants/{tenant_id}/evaluations/{evaluation_id}/inputs` | `Any tenant member` | List datasets used by the evaluation. |
| `GET` | `/api/v1/tenants/{tenant_id}/evaluations/{evaluation_id}/period-results` | `Any tenant member` | Return aggregate period or segment results for savings-over-time charts. |
| `GET` | `/api/v1/tenants/{tenant_id}/evaluations/{evaluation_id}/participant-results` | `Tenant Admin`, `Analyst`, or `Auditor` | Return participant-level or site-level results for authorized analyst drilldown. |
| `GET` | `/api/v1/tenants/{tenant_id}/evaluations/{evaluation_id}/anomalies` | `Any tenant member` | List anomalies linked to the evaluation. |
| `POST` | `/api/v1/tenants/{tenant_id}/evaluations/compare` | `Analyst` or `Auditor` | Compare two completed evaluation runs from the same tenant. |

## Alerts and Anomalies

| Method | Path | Access | Purpose |
| --- | --- | --- | --- |
| `GET` | `/api/v1/tenants/{tenant_id}/alert-rules` | `Tenant Admin` or `Analyst` | List tenant-defined alert rules for quality, usage, cost, or anomaly conditions. |
| `POST` | `/api/v1/tenants/{tenant_id}/alert-rules` | `Tenant Admin` or `Analyst` | Create an alert rule for future monitoring. |
| `GET` | `/api/v1/tenants/{tenant_id}/alert-rules/{rule_id}` | `Tenant Admin` or `Analyst` | Return one alert rule and its status. |
| `PATCH` | `/api/v1/tenants/{tenant_id}/alert-rules/{rule_id}` | `Tenant Admin` or `Analyst` | Update alert rule configuration or activation state. |
| `GET` | `/api/v1/tenants/{tenant_id}/alert-events` | `Any tenant member` | List triggered alerts with filters for status, severity, rule, and date range. |
| `POST` | `/api/v1/tenants/{tenant_id}/alert-events/{event_id}/acknowledge` | `Tenant Admin` or `Analyst` | Mark an alert event as acknowledged by an authorized user. |
| `POST` | `/api/v1/tenants/{tenant_id}/alert-events/{event_id}/resolve` | `Tenant Admin` or `Analyst` | Mark an alert event as resolved and record resolution metadata. |
| `GET` | `/api/v1/tenants/{tenant_id}/anomalies` | `Any tenant member` | List detected data or evaluation anomalies for review. |
| `GET` | `/api/v1/tenants/{tenant_id}/anomalies/{anomaly_id}` | `Any tenant member` | Return anomaly detail, severity, explanation, linked resources, and review status. |
| `POST` | `/api/v1/tenants/{tenant_id}/anomalies/{anomaly_id}/resolve` | `Tenant Admin` or `Analyst` | Resolve an anomaly after review. |

## Dashboards

Dashboard endpoints return view-ready summaries and links to the underlying
evidence records, not hidden calculations detached from lineage.

| Method | Path | Access | Purpose |
| --- | --- | --- | --- |
| `GET` | `/api/v1/tenants/{tenant_id}/dashboard/summary` | `Any tenant member` | Return executive dashboard metrics for selected programs, periods, and filters. |
| `GET` | `/api/v1/tenants/{tenant_id}/dashboard/savings-over-time` | `Any tenant member` | Return savings or impact trends over time from completed evaluations. |
| `GET` | `/api/v1/tenants/{tenant_id}/dashboard/data-quality` | `Any tenant member` | Return data-quality summary metrics, readiness indicators, and issue counts. |
| `GET` | `/api/v1/tenants/{tenant_id}/dashboard/evaluation-history` | `Any tenant member` | Return recent and historical evaluation status summaries for dashboard display. |
| `GET` | `/api/v1/tenants/{tenant_id}/dashboard/anomalies` | `Any tenant member` | Return dashboard-ready anomaly summaries and severity counts. |
| `GET` | `/api/v1/tenants/{tenant_id}/dashboard/usage` | `Tenant Admin` | Return tenant usage indicators for storage-like, processing-like, and AI-like activity. |
| `GET` | `/api/v1/tenants/{tenant_id}/dashboard/metrics/{metric_id}/evidence` | `Any tenant member` | Return the evaluation, source datasets, quality notes, assumptions, and limitations behind a displayed metric. |

## Reports and Exports

| Method | Path | Access | Purpose |
| --- | --- | --- | --- |
| `GET` | `/api/v1/tenants/{tenant_id}/reports` | `Any tenant member` | List saved report definitions and generated report history visible to the user. |
| `POST` | `/api/v1/tenants/{tenant_id}/reports` | `Tenant Admin`, `Analyst`, or `Program Manager` | Create a saved report definition for repeated use. |
| `GET` | `/api/v1/tenants/{tenant_id}/reports/{report_id}` | `Any tenant member` or `Owner` | Return saved report definition details and available runs. Private reports require owner or tenant admin access. |
| `PATCH` | `/api/v1/tenants/{tenant_id}/reports/{report_id}` | `Owner` or `Tenant Admin` | Update report definition metadata, filters, layout, or sharing state. |
| `POST` | `/api/v1/tenants/{tenant_id}/reports/{report_id}/runs` | `Tenant Admin`, `Analyst`, `Program Manager`, or `Auditor` | Generate a report from a saved definition. |
| `GET` | `/api/v1/tenants/{tenant_id}/report-runs/{run_id}` | `Any tenant member` or `Owner` | Return report generation status, export metadata, and linked file artifacts. Private report runs require owner or tenant admin access. |
| `GET` | `/api/v1/tenants/{tenant_id}/report-runs/{run_id}/download` | `Any tenant member` or `Owner` | Download an authorized generated report artifact. Private report runs require owner or tenant admin access. |
| `POST` | `/api/v1/tenants/{tenant_id}/evaluations/{evaluation_id}/summary-report` | `Tenant Admin`, `Analyst`, `Program Manager`, or `Auditor` | Generate an evaluation summary report for a completed evaluation. |
| `POST` | `/api/v1/tenants/{tenant_id}/evaluations/{evaluation_id}/evidence-package` | `Tenant Admin`, `Analyst`, or `Auditor` | Generate an evidence package containing source references, quality reports, methodology, assumptions, limitations, anomalies, and audit context. |
| `POST` | `/api/v1/tenants/{tenant_id}/evaluations/{evaluation_id}/export-results` | `Analyst` or `Auditor` | Generate a machine-readable export of evaluation results. |

## Assistant Documents

| Method | Path | Access | Purpose |
| --- | --- | --- | --- |
| `GET` | `/api/v1/tenants/{tenant_id}/assistant/documents` | `Tenant Admin` or `Analyst` | List assistant source documents with indexing status and deprecation state. |
| `POST` | `/api/v1/tenants/{tenant_id}/assistant/documents` | `Tenant Admin` | Register an uploaded document as assistant source material and start indexing workflow. |
| `GET` | `/api/v1/tenants/{tenant_id}/assistant/documents/{document_id}` | `Tenant Admin` or `Analyst` | Return assistant document metadata, indexing status, deprecation state, and source file links. |
| `PATCH` | `/api/v1/tenants/{tenant_id}/assistant/documents/{document_id}` | `Tenant Admin` | Update document metadata or review notes. Deprecation and indexing changes use explicit actions. |
| `POST` | `/api/v1/tenants/{tenant_id}/assistant/documents/{document_id}/deprecate` | `Tenant Admin` | Deprecate a document so it is not used for new assistant answers by default. |
| `POST` | `/api/v1/tenants/{tenant_id}/assistant/documents/{document_id}/reindex` | `Tenant Admin` | Rebuild assistant document chunks and embeddings for an indexed or changed document. |
| `GET` | `/api/v1/tenants/{tenant_id}/assistant/documents/{document_id}/chunks` | `Tenant Admin` or `Analyst` | List indexed chunks for document inspection and citation debugging. |
| `GET` | `/api/v1/tenants/{tenant_id}/assistant/document-flags` | `Tenant Admin` or `Analyst` | List source-content flags for unsafe, stale, sensitive, or low-quality assistant material. |
| `POST` | `/api/v1/tenants/{tenant_id}/assistant/document-flags/{flag_id}/resolve` | `Tenant Admin` | Resolve a document review flag after action or acceptance. |

## Assistant Sessions and Messages

| Method | Path | Access | Purpose |
| --- | --- | --- | --- |
| `GET` | `/api/v1/tenants/{tenant_id}/assistant/sessions` | `Any tenant member` | List the current user's assistant sessions for the tenant. Tenant admins may inspect sessions only if a governance workflow allows it. |
| `POST` | `/api/v1/tenants/{tenant_id}/assistant/sessions` | `Any tenant member` | Create a new assistant conversation session. |
| `GET` | `/api/v1/tenants/{tenant_id}/assistant/sessions/{session_id}` | `Owner` or `Tenant Admin` | Return session metadata and message history. Tenant admin access should be limited to authorized governance review. |
| `POST` | `/api/v1/tenants/{tenant_id}/assistant/sessions/{session_id}/messages` | `Owner` | Submit a user message and create a grounded assistant response or refusal. |
| `GET` | `/api/v1/tenants/{tenant_id}/assistant/messages/{message_id}/sources` | `Owner`, `Tenant Admin`, or `Auditor` | Return citations and evidence sources attached to an assistant answer. |
| `GET` | `/api/v1/tenants/{tenant_id}/assistant/interactions/{interaction_id}` | `Owner`, `Tenant Admin`, or `Auditor` | Return model-call metadata, refusal reason, retrieval summary, latency, and usage details for governance. |
| `GET` | `/api/v1/tenants/{tenant_id}/assistant/interactions/{interaction_id}/retrievals` | `Tenant Admin`, `Analyst`, or `Auditor` | Return retrieved chunks and sources considered for one assistant interaction. |
| `POST` | `/api/v1/tenants/{tenant_id}/assistant/messages/{message_id}/feedback` | `Owner` | Record user feedback on an assistant answer for quality review. |

## Assistant Evaluation

| Method | Path | Access | Purpose |
| --- | --- | --- | --- |
| `GET` | `/api/v1/tenants/{tenant_id}/assistant/evaluation-cases` | `Tenant Admin` or `Analyst` | List tenant-scoped assistant evaluation prompts and expected behaviors. |
| `POST` | `/api/v1/tenants/{tenant_id}/assistant/evaluation-cases` | `Tenant Admin` or `Analyst` | Create an assistant evaluation case for grounding, refusal, prompt-injection, or tenant-isolation checks. |
| `PATCH` | `/api/v1/tenants/{tenant_id}/assistant/evaluation-cases/{case_id}` | `Tenant Admin` or `Analyst` | Update an assistant evaluation case or activation state. |
| `POST` | `/api/v1/tenants/{tenant_id}/assistant/evaluation-runs` | `Tenant Admin` or `Analyst` | Run selected assistant evaluation cases and store pass/fail outcomes. |
| `GET` | `/api/v1/tenants/{tenant_id}/assistant/evaluation-runs` | `Tenant Admin` or `Analyst` | List assistant evaluation run history. |
| `GET` | `/api/v1/tenants/{tenant_id}/assistant/evaluation-runs/{run_id}` | `Tenant Admin` or `Analyst` | Return results for one assistant evaluation run. |

## Audit

| Method | Path | Access | Purpose |
| --- | --- | --- | --- |
| `GET` | `/api/v1/tenants/{tenant_id}/audit-logs` | `Tenant Admin` or `Auditor` | List tenant audit records with filters for user, action, entity, date, outcome, and severity. |
| `GET` | `/api/v1/tenants/{tenant_id}/audit-logs/{audit_log_id}` | `Tenant Admin` or `Auditor` | Return one audit record for detail review. |
| `POST` | `/api/v1/tenants/{tenant_id}/audit-logs/export` | `Tenant Admin` or `Auditor` | Generate an audit-log export for a filtered review set. |
| `GET` | `/api/v1/platform/audit-logs` | `Platform Admin` | List platform-level audit events for authorized platform operators. |

## Usage and Cost Awareness

| Method | Path | Access | Purpose |
| --- | --- | --- | --- |
| `GET` | `/api/v1/tenants/{tenant_id}/usage/summary` | `Tenant Admin` | Return tenant usage summary including datasets, jobs, evaluations, documents, assistant interactions, and generated exports. |
| `GET` | `/api/v1/tenants/{tenant_id}/usage/storage` | `Tenant Admin` | Return storage-like usage indicators for uploaded and generated files. |
| `GET` | `/api/v1/tenants/{tenant_id}/usage/processing` | `Tenant Admin` | Return processing volume indicators such as job counts, processed rows, failures, and retries. |
| `GET` | `/api/v1/tenants/{tenant_id}/usage/ai` | `Tenant Admin` | Return assistant usage indicators such as interaction counts, token estimates, latency, and refusal counts. |
| `GET` | `/api/v1/platform/usage/tenants` | `Platform Admin` or `Platform Operator` | Return cross-tenant usage rollups for platform administrators without exposing tenant-owned source data. |
| `GET` | `/api/v1/platform/usage/ai` | `Platform Admin` or `Platform Operator` | Return cross-tenant AI usage and cost indicators for platform operations. |

## Platform Operations

| Method | Path | Access | Purpose |
| --- | --- | --- | --- |
| `GET` | `/api/v1/health` | `Public` | Return basic API health for uptime checks. |
| `GET` | `/api/v1/ready` | `Platform Operator`, `Platform Admin`, or restricted health-check identity | Return readiness status for dependencies required to serve traffic. |
| `GET` | `/api/v1/platform/health` | `Platform Admin` or `Platform Operator` | Return platform health indicators for authorized operators, including job failures, processing delays, assistant errors, and recent system activity. |
| `GET` | `/api/v1/platform/jobs` | `Platform Admin` or `Platform Operator` | List recent background jobs across tenants with tenant-safe operational metadata. |
| `GET` | `/api/v1/platform/jobs/{job_id}` | `Platform Admin` or `Platform Operator` | Return operational detail for a background job when the operator is authorized to inspect it. |

## Open Questions

- Should tenant URLs use `tenant_id` only, or should the frontend route by tenant
  slug while the API resolves to immutable tenant IDs?
- Should uploads use a two-step pre-signed URL flow for every file type, or can
  small public-demo files be uploaded directly through the API gateway?
- Which assistant endpoints should support streaming responses in the first
  implementation?
- Which operational data browsing endpoints should be promoted from read-only
  to write-capable once manual editing workflows are defined?
- Should audit exports be synchronous for small result sets or always handled as
  report/export runs?
- Should authorization be implemented as role checks only, or should roles map
  to named permissions such as `datasets:write`, `evaluations:approve`, and
  `audit:export`?
