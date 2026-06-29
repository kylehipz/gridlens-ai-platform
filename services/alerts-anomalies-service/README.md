# Alerts Anomalies Service

Owns alert rules, triggered alert events, anomaly review workflows, and
resolution metadata.

## Ownership

- Alert rule configuration and lifecycle.
- Triggered alert event status, acknowledgement, and resolution.
- Anomaly review and resolution workflows not owned by evaluation internals.
- Cross-service anomaly surfaces that remain tenant-scoped server-side.

## Key Endpoints

- `GET /health` and `GET /healthz`: scaffold health endpoints.
- Planned alert rule, alert event, and anomaly routes are described in
  `docs/api/endpoints.md`.

## Tables

Migrations are deferred. Expected ownership includes alert rules, alert events,
anomalies, acknowledgement records, resolution records, and notification
metadata.

## Workers

No async worker is active in this scaffold. The `workers/` package is reserved
for future alert evaluation, notification, and anomaly-maintenance jobs.

## Flow Diagrams

Detailed alert triggering and anomaly review flow diagrams are deferred until
alert evaluation jobs and persistence are implemented.
