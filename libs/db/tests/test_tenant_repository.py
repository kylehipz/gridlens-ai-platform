import os
import unittest
from dataclasses import dataclass
from importlib import import_module
from uuid import UUID

from gridlens_db import TenantMembershipRepository, TenantScopedRepository
from gridlens_db.models import (
    app_users,
    audit_logs,
    file_objects,
    metadata,
    platform_role_assignments,
    tenant_memberships,
    tenants,
)
from gridlens_db.seed import (
    AUDIT_LOG_ROWS,
    CASCADE_TENANT_ID,
    JORDAN_USER_ID,
    KYLE_USER_ID,
    MEMBERSHIP_ROWS,
    NORTHWIND_TENANT_ID,
    PLATFORM_ROLE_ASSIGNMENT_ROWS,
    TENANT_ROWS,
    USER_ROWS,
)
from gridlens_db.tenant_repository import (
    active_platform_roles_for_user_statement,
    app_user_external_identity_statement,
    membership_lookup_statement,
    membership_user_tenant_statement,
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
                    "role": "Analyst",
                    "status": "active",
                }
            ]
        )
        records = TenantMembershipRepository(session).list_for_tenant(NORTHWIND_TENANT_ID)
        self.assertEqual(["Analyst"], [record.role for record in records])
        self.assertEqual(NORTHWIND_TENANT_ID, records[0].tenant_id)

    def test_membership_repository_maps_external_subject_to_user(self):
        session = SessionStub(
            [
                {
                    "id": JORDAN_USER_ID,
                    "email": "jordan.lee@kylehipz.dev",
                    "display_name": "Jordan Lee",
                    "external_auth_provider": "cognito",
                    "external_subject": "dev-jordan-lee",
                    "status": "active",
                }
            ]
        )
        user = TenantMembershipRepository(session).get_user_by_external_identity(
            "cognito", "dev-jordan-lee"
        )
        self.assertIsNotNone(user)
        assert user is not None
        self.assertEqual(JORDAN_USER_ID, user.id)
        self.assertEqual("cognito", user.external_auth_provider)
        statement = session.statements[0][0]
        self.assertIn("app_users.external_auth_provider = :external_auth_provider_1", str(statement))
        self.assertIn("app_users.external_subject = :external_subject_1", str(statement))

    def test_membership_repository_maps_user_tenant_membership(self):
        session = SessionStub(
            [
                {
                    "id": UUID("30000000-0000-4000-8000-000000000001"),
                    "tenant_id": NORTHWIND_TENANT_ID,
                    "user_id": JORDAN_USER_ID,
                    "role": "Analyst",
                    "status": "active",
                }
            ]
        )
        membership = TenantMembershipRepository(session).get_membership_for_user_tenant(
            user_id=JORDAN_USER_ID, tenant_id=NORTHWIND_TENANT_ID
        )
        self.assertIsNotNone(membership)
        assert membership is not None
        self.assertEqual("Analyst", membership.role)
        statement = session.statements[0][0]
        self.assertIn("tenant_memberships.user_id = :user_id_1", str(statement))
        self.assertIn("tenant_memberships.tenant_id = :tenant_id_1", str(statement))

    def test_membership_repository_maps_active_platform_roles(self):
        session = SessionStub(
            [
                {
                    "id": UUID("31000000-0000-4000-8000-000000000001"),
                    "user_id": KYLE_USER_ID,
                    "role": "Platform Admin",
                    "status": "active",
                }
            ]
        )

        roles = TenantMembershipRepository(session).list_active_platform_roles_for_user(KYLE_USER_ID)

        self.assertEqual(["Platform Admin"], [role.role for role in roles])
        statement = session.statements[0][0]
        self.assertIn("platform_role_assignments.user_id = :user_id_1", str(statement))
        self.assertIn("platform_role_assignments.status = :status_1", str(statement))


class SchemaMetadataTests(unittest.TestCase):
    def test_t07_tables_are_present_in_app_schema(self):
        self.assertEqual("app", metadata.schema)
        self.assertTrue(
            {
                "app.tenants",
                "app.app_users",
                "app.tenant_memberships",
                "app.platform_role_assignments",
                "app.file_objects",
                "app.audit_logs",
            }.issubset(metadata.tables)
        )

    def test_tenant_owned_tables_carry_tenant_id(self):
        self.assertIn("tenant_id", tenant_memberships.c)
        self.assertIn("tenant_id", file_objects.c)
        self.assertIn("tenant_id", audit_logs.c)
        self.assertNotIn("tenant_id", metadata.tables["app.app_users"].c)
        self.assertNotIn("tenant_id", metadata.tables["app.platform_role_assignments"].c)

    def test_memberships_prevent_duplicate_user_tenant_pairs(self):
        unique_columns = {
            tuple(column.name for column in constraint.columns)
            for constraint in tenant_memberships.constraints
            if isinstance(constraint, UniqueConstraint)
        }
        self.assertIn(("tenant_id", "user_id"), unique_columns)

    def test_platform_roles_prevent_duplicate_user_role_pairs(self):
        unique_columns = {
            tuple(column.name for column in constraint.columns)
            for constraint in platform_role_assignments.constraints
            if isinstance(constraint, UniqueConstraint)
        }
        self.assertIn(("user_id", "role"), unique_columns)

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
            "ix_platform_role_assignments_user_id_status",
            {index.name for index in platform_role_assignments.indexes},
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
        self.assertIn("tenant_memberships.tenant_id", membership_sql)
        app_user_sql = str(
            app_user_external_identity_statement("cognito", "dev-jordan-lee").compile(
                dialect=postgresql.dialect()
            )
        )
        user_tenant_sql = str(
            membership_user_tenant_statement(
                user_id=JORDAN_USER_ID, tenant_id=NORTHWIND_TENANT_ID
            ).compile(dialect=postgresql.dialect())
        )
        platform_role_sql = str(
            active_platform_roles_for_user_statement(KYLE_USER_ID).compile(dialect=postgresql.dialect())
        )
        self.assertIn("app_users.external_auth_provider", app_user_sql)
        self.assertIn("app_users.external_subject", app_user_sql)
        self.assertIn("tenant_memberships.user_id", user_tenant_sql)
        self.assertIn("tenant_memberships.tenant_id", user_tenant_sql)
        self.assertIn("platform_role_assignments.user_id", platform_role_sql)
        self.assertIn("platform_role_assignments.status", platform_role_sql)

    def test_seed_data_has_required_tenants_and_role_variation(self):
        self.assertEqual({"Northwind Utilities", "Cascade Water District"}, {row["name"] for row in TENANT_ROWS})
        self.assertEqual(CASCADE_TENANT_ID, TENANT_ROWS[1]["id"])
        self.assertIn("jordan.lee@kylehipz.dev", {row["email"] for row in USER_ROWS})
        self.assertIn("kyle@kylehipz.dev", {row["email"] for row in USER_ROWS})
        self.assertEqual(
            [{"user_id": KYLE_USER_ID, "role": "Platform Admin", "status": "active"}],
            [
                {key: row[key] for key in ("user_id", "role", "status")}
                for row in PLATFORM_ROLE_ASSIGNMENT_ROWS
            ],
        )
        self.assertNotIn(KYLE_USER_ID, {row["user_id"] for row in MEMBERSHIP_ROWS})
        self.assertEqual(
            {KYLE_USER_ID},
            {row["actor_user_id"] for row in AUDIT_LOG_ROWS if row["action"] == "tenant.created"},
        )
        jordan_roles = {
            row["tenant_id"]: row["role"] for row in MEMBERSHIP_ROWS if row["user_id"] == JORDAN_USER_ID
        }
        self.assertEqual(
            {
                NORTHWIND_TENANT_ID: "Analyst",
                CASCADE_TENANT_ID: "Viewer",
            },
            jordan_roles,
        )

    def test_initial_rls_protects_tenant_owned_tables(self):
        self.assertEqual(
            {
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
