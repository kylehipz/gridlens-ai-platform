# Governance Service

Owns audit views, platform operational governance, policy surfaces, and
cross-service compliance support.

## Ownership

- Tenant and platform audit query surfaces.
- Governance views over jobs, AI activity, policy decisions, and operational
  metadata.
- Compliance-support workflows that coordinate with service-owned audit events.

## Key Endpoints

- `GET /health` and `GET /healthz`: scaffold health endpoints.
- Planned audit and governance routes are described in `docs/api/endpoints.md`
  as the audit and operational surfaces are refined.

## Tables

Migrations are deferred. Expected ownership includes governance read models and
audit query projections. Source audit event tables may be shared through
contracts or owned by this service in a later migration workstream.

## Workers

No async worker is active in this scaffold. The `workers/` package is reserved
for future audit projection or policy-maintenance jobs.

## Flow Diagrams

Detailed governance and audit flow diagrams are deferred until audit event
storage and policy decisions are implemented.
