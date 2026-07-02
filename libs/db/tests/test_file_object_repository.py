import unittest
from uuid import UUID

from gridlens_db.file_object_repository import FileObjectRepository, file_object_lookup_statement
from gridlens_db.seed import JORDAN_USER_ID, NORTHWIND_TENANT_ID
from sqlalchemy.dialects import postgresql


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


class FileObjectRepositoryTests(unittest.TestCase):
    def test_filters_lookup_by_tenant(self):
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

    def test_maps_same_tenant_rows(self):
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

    def test_lookup_statement_includes_tenant_predicate(self):
        file_sql = str(
            file_object_lookup_statement(
                NORTHWIND_TENANT_ID, UUID("40000000-0000-4000-8000-000000000001")
            ).compile(dialect=postgresql.dialect())
        )

        self.assertIn("file_objects.tenant_id", file_sql)


if __name__ == "__main__":
    unittest.main()
