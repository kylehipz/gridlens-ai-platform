# GridLens DB

Framework-neutral database metadata, migration, seed, and repository helpers.

## Schema and Migrations

SQLAlchemy table metadata lives in `libs/db/src/gridlens_db/models.py`.
Alembic migrations live under `infra/db/alembic/` and are run from the repo
root:

```sh
make migrate
```

`make migrate` uses `DATABASE_URL` when set. Without `DATABASE_URL`, it targets
the local host PostgreSQL defaults from the root `Makefile`.

The T07 baseline schema creates:

- `app.tenants`
- `app.app_users`
- `app.tenant_memberships`
- `app.file_objects`
- `app.audit_logs`

`app_users` is global identity metadata. Memberships, file objects, audit logs,
and tenant rows are tenant-owned and protected by initial PostgreSQL RLS
policies that read the `app.tenant_id` session setting.

## Seed Data

Run deterministic synthetic seed data after migrations:

```sh
make seed
```

Seed rows use fixed UUIDs and PostgreSQL upserts, so the command can be run
repeatedly without duplicate rows. The seed data includes `Northwind Utilities`,
`Cascade Water District`, synthetic users, tenant memberships, file metadata,
and audit rows for `tenant.created` and `authorization.denied`.

Seed values must remain public-safe: do not add real customer names, real
emails, credentials, regulated data, or production exports.

## Tenant Session Settings

Tenant-owned queries must set the tenant context before reading or writing
tenant rows:

```sql
select set_config('app.tenant_id', '<tenant_uuid>', true);
```

`RlsSessionContext` exposes the current `app.tenant_id`, `app.actor_id`, and
`app.request_id` settings for SQLAlchemy connections. PostgreSQL RLS is a
backstop; application repositories still filter by tenant explicitly.

## Repositories

`TenantMembershipRepository` and `FileObjectRepository` accept a SQLAlchemy
session or connection-like object and always include tenant predicates in
lookup/list statements. Cross-tenant lookups return no rows and raise
`LookupError` at the repository boundary.

Fast in-memory tenant-scoping tests remain available through
`TenantScopedRepository` for offline coverage.
