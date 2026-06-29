# Insights Reporting Service

Owns dashboards, evidence packages, generated summaries, exports, scheduled
reports, and reporting lineage.

## Ownership

- Dashboard-ready summaries and evidence links.
- Report generation and export lifecycle.
- Scheduled report definitions and delivery status.
- Reporting lineage that connects outputs to evaluations and source data.

## Key Endpoints

- `GET /health` and `GET /healthz`: scaffold health endpoints.
- Planned dashboard, report, export, and evidence routes are described in
  `docs/api/endpoints.md`.

## Tables

Migrations are deferred. Expected ownership includes dashboard snapshots,
reports, exports, schedules, generated summary metadata, and evidence packages.

## Workers

`gridlens_insights_reporting_service.workers.main` exposes deterministic
readiness for future report generation and export workers. The placeholder does
not poll queues, call storage, or send notifications.

## Flow Diagrams

Detailed report generation, export, and schedule flow diagrams are deferred
until those workflows are implemented.
