import unittest
from dataclasses import dataclass

from gridlens_db import TenantScopedRepository
from gridlens_db.tenant_repository import RlsSessionContext
from gridlens_testing import make_tenant, make_user


@dataclass(frozen=True)
class Record:
    id: str
    tenant_id: str
    value: str


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

    def test_rls_session_context_exposes_future_postgres_settings(self):
        settings = RlsSessionContext("tenant_a", "user_a", "req_1").settings()
        self.assertEqual("tenant_a", settings["app.tenant_id"])


if __name__ == "__main__":
    unittest.main()
