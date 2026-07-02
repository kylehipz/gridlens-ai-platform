# GridLens DB

Framework-neutral database metadata, migration, seed, and repository helpers.

## Schema and Migrations

SQLAlchemy table metadata lives in `libs/db/src/gridlens_db/models.py`.
Alembic migrations live under `infra/db/alembic/` and are run from the repo
root:

```sh
make migrate
```

`make migrate` uses `MIGRATION_DATABASE_URL` when set. Without
`MIGRATION_DATABASE_URL`, it targets the local host PostgreSQL migrator defaults
from `gridlens_db.database`.

Runtime code and `make seed` use `DATABASE_URL`, which should point at the
lower-privilege `gridlens_app` role. Alembic migrations use the
`gridlens_migrator` role so schema ownership and runtime access stay separate.
The default `make seed` target runs inside the Compose DB utility container, so
values from `.env` are loaded by Compose and `postgres` resolves on the local
Compose network.

The current app schema includes:

- `app.tenants`
- `app.app_users`
- `app.tenant_memberships`
- `app.platform_role_assignments`
- `app.file_objects`
- `app.audit_logs`

`app_users` is global identity metadata. `tenants` and `tenant_memberships`
remain outside tenant-scoped RLS so platform admins can create tenants and
assign access before they belong to any tenant. Platform roles are persisted in
`platform_role_assignments`; Cognito is authentication-only. `file_objects` and
`audit_logs` are protected by initial PostgreSQL RLS policies that read the
`app.tenant_id` session setting. Application repositories still filter and
authorize tenant access explicitly; RLS is the database backstop for
tenant-owned rows.

## Seed Data

Run deterministic synthetic seed data after migrations:

```sh
make seed
```

Seed rows use fixed UUIDs and PostgreSQL upserts, so the command can be run
repeatedly without duplicate rows. The seed data includes `Northwind Utilities`,
`Cascade Water District`, synthetic users, Kyle as a platform admin, tenant
memberships, file metadata, and audit rows for `tenant.created` and
`authorization.denied`.

Seed values must remain public-safe: do not add real customer names, real
emails, credentials, regulated data, or production exports.

## Tenant Session Settings

Tenant-scoped queries must set the tenant context before reading or writing
RLS-protected rows:

```sql
select set_config('app.tenant_id', '<tenant_uuid>', true);
```

`gridlens_db.rls.RlsSessionContext` exposes the current `app.tenant_id`,
`app.actor_id`, and `app.request_id` settings for SQLAlchemy connections.
PostgreSQL RLS is a backstop; application repositories still filter by tenant
explicitly.

## Repositories

Repository modules are grouped by the domain records they own.
`TenantMembershipRepository` handles identity and membership lookups, while
`FileObjectRepository` handles file metadata lookups. Both accept a SQLAlchemy
session or connection-like object and include tenant predicates in lookup/list
statements. Cross-tenant lookups return no rows and raise `LookupError` at the
repository boundary.

Fast in-memory tenant-scoping tests remain available through
`TenantScopedRepository` for offline coverage.
