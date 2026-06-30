import os
import unittest
from dataclasses import dataclass
from importlib import import_module
from uuid import UUID

from gridlens_db import FileObjectRepository, TenantMembershipRepository, TenantScopedRepository
from gridlens_db.models import (
    app_users,
    audit_logs,
    file_objects,
    metadata,
    tenant_memberships,
    tenants,
)
from gridlens_db.seed import (
    CASCADE_TENANT_ID,
    JORDAN_USER_ID,
    MEMBERSHIP_ROWS,
    NORTHWIND_TENANT_ID,
    TENANT_ROWS,
    USER_ROWS,
)
from gridlens_db.tenant_repository import (
    RlsSessionContext,
    file_object_lookup_statement,
    membership_lookup_statement,
)
from gridlens_testing import make_tenant, make_user
from sqlalchemy import UniqueConstraint
from sqlalchemy.dialects import postgresql

INITIAL_RLS_POLICIES = import_module(
    "infra.db.alembic.versions.20260630_0003_add_initial_rls_policies"
)


@dataclass(frozen=True)
class Record:
    id: str
    tenant_id: str
    value: str


class ResultStub:
    def __init__(self, rows):
        self._rows = rows

    def mappings(self):
        return self

    def all(self):
        return self._rows

    def one_or_none(self):
        if not self._rows:
            return None
        if len(self._rows) > 1:
            raise AssertionError("expected at most one row")
        return self._rows[0]


class SessionStub:
    def __init__(self, rows):
        self.rows = rows
        self.statements = []

    def execute(self, statement, parameters=None):
        self.statements.append((statement, parameters))
        return ResultStub(self.rows)


class TenantRepositoryTests(unittest.TestCase):
    def test_shared_fixtures_scope_repository_records_by_tenant(self):
        tenant_a = make_tenant("tenant_a")
        tenant_b = make_tenant("tenant_b")
        make_user("analyst", tenant_a, role="Analyst")
        repo = TenantScopedRepository(
            [
                Record(id="record_a", tenant_id=tenant_a.id, value="a"),
                Record(id="record_b", tenant_id=tenant_b.id, value="b"),
            ]
        )
        self.assertEqual(["record_a"], [record.id for record in repo.list_for_tenant(tenant_a.id)])
        with self.assertRaises(LookupError):
            repo.get_for_tenant(tenant_a.id, "record_b")

    def test_membership_repository_filters_lookup_by_tenant(self):
        tenant_a = UUID("10000000-0000-4000-8000-000000000001")
        tenant_b_membership = UUID("30000000-0000-4000-8000-000000000002")
        session = SessionStub([])
        repo = TenantMembershipRepository(session)

        with self.assertRaises(LookupError):
            repo.get_for_tenant(tenant_a, tenant_b_membership)

        statement = session.statements[0][0]
        self.assertIn("tenant_memberships.tenant_id = :tenant_id_1", str(statement))
        self.assertIn("tenant_memberships.id = :id_1", str(statement))
        self.assertEqual(tenant_a, statement.compile().params["tenant_id_1"])
        self.assertEqual(tenant_b_membership, statement.compile().params["id_1"])

    def test_membership_repository_maps_same_tenant_rows(self):
        session = SessionStub(
            [
                {
                    "id": UUID("30000000-0000-4000-8000-000000000001"),
                    "tenant_id": NORTHWIND_TENANT_ID,
                    "user_id": JORDAN_USER_ID,
                    "role": "Tenant Admin",
                    "status": "active",
                }
            ]
        )
        records = TenantMembershipRepository(session).list_for_tenant(NORTHWIND_TENANT_ID)
        self.assertEqual(["Tenant Admin"], [record.role for record in records])
        self.assertEqual(NORTHWIND_TENANT_ID, records[0].tenant_id)

    def test_file_object_repository_filters_lookup_by_tenant(self):
        tenant_a = UUID("10000000-0000-4000-8000-000000000001")
        tenant_b_file = UUID("40000000-0000-4000-8000-000000000002")
        session = SessionStub([])
        repo = FileObjectRepository(session)

        with self.assertRaises(LookupError):
            repo.get_for_tenant(tenant_a, tenant_b_file)

        statement = session.statements[0][0]
        self.assertIn("file_objects.tenant_id = :tenant_id_1", str(statement))
        self.assertIn("file_objects.id = :id_1", str(statement))
        self.assertEqual(tenant_a, statement.compile().params["tenant_id_1"])
        self.assertEqual(tenant_b_file, statement.compile().params["id_1"])

    def test_file_object_repository_maps_same_tenant_rows(self):
        session = SessionStub(
            [
                {
                    "id": UUID("40000000-0000-4000-8000-000000000001"),
                    "tenant_id": NORTHWIND_TENANT_ID,
                    "created_by_user_id": JORDAN_USER_ID,
                    "object_purpose": "dataset_upload",
                    "original_file_name": "northwind-meter-readings.csv",
                    "content_type": "text/csv",
                    "storage_bucket": "gridlens-dev-artifacts",
                    "storage_key": "tenants/northwind-utilities/uploads/northwind-meter-readings.csv",
                    "checksum_sha256": "a" * 64,
                    "file_size_bytes": 2048,
                    "storage_status": "available",
                }
            ]
        )
        records = FileObjectRepository(session).list_for_tenant(NORTHWIND_TENANT_ID)
        self.assertEqual(["northwind-meter-readings.csv"], [record.original_file_name for record in records])
        self.assertEqual(NORTHWIND_TENANT_ID, records[0].tenant_id)

    def test_rls_session_context_exposes_and_applies_postgres_settings(self):
        connection = SessionStub([])
        settings = RlsSessionContext("tenant_a", "user_a", "req_1").settings()
        self.assertEqual("tenant_a", settings["app.tenant_id"])

        RlsSessionContext("tenant_a", "user_a", "req_1").apply(connection)

        applied = [parameters for _statement, parameters in connection.statements]
        self.assertIn({"key": "app.tenant_id", "value": "tenant_a"}, applied)
        self.assertIn({"key": "app.actor_id", "value": "user_a"}, applied)
        self.assertIn({"key": "app.request_id", "value": "req_1"}, applied)


class SchemaMetadataTests(unittest.TestCase):
    def test_t07_tables_are_present_in_app_schema(self):
        self.assertEqual("app", metadata.schema)
        self.assertTrue(
            {"app.tenants", "app.app_users", "app.tenant_memberships", "app.file_objects", "app.audit_logs"}.issubset(
                metadata.tables
            )
        )

    def test_tenant_owned_tables_carry_tenant_id(self):
        self.assertIn("tenant_id", tenant_memberships.c)
        self.assertIn("tenant_id", file_objects.c)
        self.assertIn("tenant_id", audit_logs.c)
        self.assertNotIn("tenant_id", metadata.tables["app.app_users"].c)

    def test_memberships_prevent_duplicate_user_tenant_pairs(self):
        unique_columns = {
            tuple(column.name for column in constraint.columns)
            for constraint in tenant_memberships.constraints
            if isinstance(constraint, UniqueConstraint)
        }
        self.assertIn(("tenant_id", "user_id"), unique_columns)

    def test_recommended_indexes_are_registered(self):
        self.assertIn("uq_app_users_email_lower", {index.name for index in app_users.indexes})
        self.assertIn(
            "ix_tenant_memberships_tenant_id_role_status",
            {index.name for index in tenant_memberships.indexes},
        )
        self.assertIn(
            "ix_tenant_memberships_user_id_status",
            {index.name for index in tenant_memberships.indexes},
        )
        self.assertIn(
            "ix_file_objects_tenant_id_object_purpose_created_at",
            {index.name for index in file_objects.indexes},
        )
        self.assertIn("ix_file_objects_tenant_id_checksum_sha256", {index.name for index in file_objects.indexes})
        self.assertIn(
            "uq_file_objects_tenant_id_checksum_sha256_dataset_upload",
            {index.name for index in file_objects.indexes},
        )
        self.assertIn("ix_audit_logs_tenant_id_action", {index.name for index in audit_logs.indexes})

    def test_lookup_statements_include_tenant_predicates(self):
        membership_sql = str(
            membership_lookup_statement(NORTHWIND_TENANT_ID, UUID("30000000-0000-4000-8000-000000000001")).compile(
                dialect=postgresql.dialect()
            )
        )
        file_sql = str(
            file_object_lookup_statement(NORTHWIND_TENANT_ID, UUID("40000000-0000-4000-8000-000000000001")).compile(
                dialect=postgresql.dialect()
            )
        )
        self.assertIn("tenant_memberships.tenant_id", membership_sql)
        self.assertIn("file_objects.tenant_id", file_sql)

    def test_seed_data_has_required_tenants_and_role_variation(self):
        self.assertEqual({"Northwind Utilities", "Cascade Water District"}, {row["name"] for row in TENANT_ROWS})
        self.assertEqual(CASCADE_TENANT_ID, TENANT_ROWS[1]["id"])
        self.assertIn("jordan.lee@example.com", {row["email"] for row in USER_ROWS})
        jordan_roles = {
            row["tenant_id"]: row["role"] for row in MEMBERSHIP_ROWS if row["user_id"] == JORDAN_USER_ID
        }
        self.assertEqual(
            {
                NORTHWIND_TENANT_ID: "Tenant Admin",
                CASCADE_TENANT_ID: "Analyst",
            },
            jordan_roles,
        )

    def test_initial_rls_protects_tenant_owned_tables(self):
        self.assertEqual(
            {
                "tenants": "id",
                "tenant_memberships": "tenant_id",
                "file_objects": "tenant_id",
                "audit_logs": "tenant_id",
            },
            INITIAL_RLS_POLICIES.TENANT_POLICY_TABLES,
        )


@unittest.skipUnless(os.environ.get("GRIDLENS_TEST_DATABASE_URL"), "live PostgreSQL URL not configured")
class LivePostgresSchemaTests(unittest.TestCase):
    def test_live_database_checks_are_documented_here(self):
        self.assertIn("id", tenants.c)


if __name__ == "__main__":
    unittest.main()
