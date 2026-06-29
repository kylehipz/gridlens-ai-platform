# Identity Tenant Service

Owns tenant identity, membership, role, invitation, tenant setting, and feature
flag workflows.

## Ownership

- Tenant workspace lifecycle and tenant settings.
- User membership and invitation lifecycle.
- Role and permission surfaces that other services consume through contracts.
- Server-side tenant context validation when product routes are implemented.

## Key Endpoints

- `GET /health` and `GET /healthz`: scaffold health endpoints.
- Planned `/api/v1/me`, `/api/v1/me/tenants`, `/api/v1/tenants`, and
  `/api/v1/tenants/{tenant_id}/members` routes are described in
  `docs/api/endpoints.md`.

## Tables

Migrations are deferred. Expected ownership includes tenants, users,
memberships, invitations, tenant settings, and feature flags.

## Workers

No async worker is active in this scaffold. The `workers/` package is reserved
for future invitation expiry, membership synchronization, or identity event
handlers.

## Flow Diagrams

Detailed identity and tenant flow diagrams are deferred until the first product
routes and migrations are implemented.
