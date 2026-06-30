from __future__ import annotations

from collections.abc import Iterable, Mapping, Sequence
from typing import Any
from uuid import UUID

from sqlalchemy import Table, text
from sqlalchemy.dialects.postgresql import insert

from gridlens_db.database import create_database_engine
from gridlens_db.models import app_users, audit_logs, file_objects, tenant_memberships, tenants

NORTHWIND_TENANT_ID = UUID("10000000-0000-4000-8000-000000000001")
CASCADE_TENANT_ID = UUID("10000000-0000-4000-8000-000000000002")

JORDAN_USER_ID = UUID("20000000-0000-4000-8000-000000000001")
PRIYA_USER_ID = UUID("20000000-0000-4000-8000-000000000002")
MARCUS_USER_ID = UUID("20000000-0000-4000-8000-000000000003")

TENANT_ROWS: list[dict[str, Any]] = [
    {
        "id": NORTHWIND_TENANT_ID,
        "name": "Northwind Utilities",
        "slug": "northwind-utilities",
        "status": "active",
        "preferences_json": {"timezone": "America/Chicago", "unit_system": "us"},
    },
    {
        "id": CASCADE_TENANT_ID,
        "name": "Cascade Water District",
        "slug": "cascade-water-district",
        "status": "active",
        "preferences_json": {"timezone": "America/Los_Angeles", "unit_system": "us"},
    },
]

USER_ROWS: list[dict[str, Any]] = [
    {
        "id": JORDAN_USER_ID,
        "email": "jordan.lee@example.com",
        "display_name": "Jordan Lee",
        "external_auth_provider": "cognito",
        "external_subject": "dev-jordan-lee",
        "status": "active",
    },
    {
        "id": PRIYA_USER_ID,
        "email": "priya.raman@example.com",
        "display_name": "Priya Raman",
        "external_auth_provider": "cognito",
        "external_subject": "dev-priya-raman",
        "status": "active",
    },
    {
        "id": MARCUS_USER_ID,
        "email": "marcus.brooks@example.com",
        "display_name": "Marcus Brooks",
        "external_auth_provider": "cognito",
        "external_subject": "dev-marcus-brooks",
        "status": "active",
    },
]

MEMBERSHIP_ROWS: list[dict[str, Any]] = [
    {
        "id": UUID("30000000-0000-4000-8000-000000000001"),
        "tenant_id": NORTHWIND_TENANT_ID,
        "user_id": JORDAN_USER_ID,
        "role": "tenant_admin",
        "status": "active",
    },
    {
        "id": UUID("30000000-0000-4000-8000-000000000002"),
        "tenant_id": CASCADE_TENANT_ID,
        "user_id": JORDAN_USER_ID,
        "role": "analyst",
        "status": "active",
    },
    {
        "id": UUID("30000000-0000-4000-8000-000000000003"),
        "tenant_id": NORTHWIND_TENANT_ID,
        "user_id": PRIYA_USER_ID,
        "role": "program_manager",
        "status": "active",
    },
    {
        "id": UUID("30000000-0000-4000-8000-000000000004"),
        "tenant_id": CASCADE_TENANT_ID,
        "user_id": MARCUS_USER_ID,
        "role": "viewer",
        "status": "active",
    },
]

FILE_OBJECT_ROWS: list[dict[str, Any]] = [
    {
        "id": UUID("40000000-0000-4000-8000-000000000001"),
        "tenant_id": NORTHWIND_TENANT_ID,
        "created_by_user_id": PRIYA_USER_ID,
        "object_purpose": "dataset_upload",
        "original_file_name": "northwind-meter-readings.csv",
        "content_type": "text/csv",
        "storage_bucket": "gridlens-dev-artifacts",
        "storage_key": "tenants/northwind-utilities/uploads/northwind-meter-readings.csv",
        "checksum_sha256": "a" * 64,
        "file_size_bytes": 2048,
        "storage_status": "available",
    },
    {
        "id": UUID("40000000-0000-4000-8000-000000000002"),
        "tenant_id": CASCADE_TENANT_ID,
        "created_by_user_id": MARCUS_USER_ID,
        "object_purpose": "assistant_document",
        "original_file_name": "cascade-program-guide.pdf",
        "content_type": "application/pdf",
        "storage_bucket": "gridlens-dev-artifacts",
        "storage_key": "tenants/cascade-water-district/documents/cascade-program-guide.pdf",
        "checksum_sha256": "b" * 64,
        "file_size_bytes": 4096,
        "storage_status": "available",
    },
]

AUDIT_LOG_ROWS: list[dict[str, Any]] = [
    {
        "id": UUID("50000000-0000-4000-8000-000000000001"),
        "tenant_id": NORTHWIND_TENANT_ID,
        "actor_user_id": JORDAN_USER_ID,
        "action": "tenant.created",
        "outcome": "success",
        "severity": "info",
        "target_type": "tenant",
        "target_id": str(NORTHWIND_TENANT_ID),
        "request_id": "seed-northwind-tenant-created",
        "metadata_json": {"source": "seed"},
    },
    {
        "id": UUID("50000000-0000-4000-8000-000000000002"),
        "tenant_id": CASCADE_TENANT_ID,
        "actor_user_id": JORDAN_USER_ID,
        "action": "tenant.created",
        "outcome": "success",
        "severity": "info",
        "target_type": "tenant",
        "target_id": str(CASCADE_TENANT_ID),
        "request_id": "seed-cascade-tenant-created",
        "metadata_json": {"source": "seed"},
    },
    {
        "id": UUID("50000000-0000-4000-8000-000000000003"),
        "tenant_id": CASCADE_TENANT_ID,
        "actor_user_id": MARCUS_USER_ID,
        "action": "authorization.denied",
        "outcome": "denied",
        "severity": "warning",
        "target_type": "file_object",
        "target_id": str(UUID("40000000-0000-4000-8000-000000000001")),
        "request_id": "seed-cross-tenant-denied",
        "metadata_json": {"reason": "cross_tenant_access", "source": "seed"},
    },
]


def _upsert_rows(
    connection: Any,
    table: Table,
    rows: Iterable[Mapping[str, Any]],
    conflict_columns: list[str],
) -> None:
    row_list = list(rows)
    if not row_list:
        return

    statement = insert(table).values(row_list)
    update_columns = {
        column.name: getattr(statement.excluded, column.name)
        for column in table.columns
        if not column.primary_key and column.name in row_list[0]
    }
    connection.execute(
        statement.on_conflict_do_update(
            index_elements=[table.c[column_name] for column_name in conflict_columns],
            set_=update_columns,
        )
    )


def _set_tenant(connection: Any, tenant_id: UUID) -> None:
    connection.execute(text("select set_config('app.tenant_id', :tenant_id, true)"), {"tenant_id": str(tenant_id)})


def _seed_tenant_owned_rows(connection: Any, table: Table, rows: Sequence[Mapping[str, Any]]) -> None:
    for tenant_id in sorted({row["tenant_id"] for row in rows}, key=str):
        _set_tenant(connection, tenant_id)
        tenant_rows = [row for row in rows if row["tenant_id"] == tenant_id]
        _upsert_rows(connection, table, tenant_rows, ["id"])


def seed_database() -> None:
    engine = create_database_engine()
    with engine.begin() as connection:
        _upsert_rows(connection, tenants, TENANT_ROWS, ["id"])
        _upsert_rows(connection, app_users, USER_ROWS, ["id"])
        _upsert_rows(connection, tenant_memberships, MEMBERSHIP_ROWS, ["id"])
        _seed_tenant_owned_rows(connection, file_objects, FILE_OBJECT_ROWS)
        _seed_tenant_owned_rows(connection, audit_logs, AUDIT_LOG_ROWS)


def main() -> None:
    seed_database()


if __name__ == "__main__":
    main()
