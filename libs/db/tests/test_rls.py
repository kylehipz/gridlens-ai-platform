import unittest

from gridlens_db.rls import RlsSessionContext


class SessionStub:
    def __init__(self):
        self.statements = []

    def execute(self, statement, parameters=None):
        self.statements.append((statement, parameters))


class RlsSessionContextTests(unittest.TestCase):
    def test_exposes_and_applies_postgres_settings(self):
        connection = SessionStub()
        settings = RlsSessionContext("tenant_a", "user_a", "req_1").settings()
        self.assertEqual("tenant_a", settings["app.tenant_id"])

        RlsSessionContext("tenant_a", "user_a", "req_1").apply(connection)

        applied = [parameters for _statement, parameters in connection.statements]
        self.assertIn({"key": "app.tenant_id", "value": "tenant_a"}, applied)
        self.assertIn({"key": "app.actor_id", "value": "user_a"}, applied)
        self.assertIn({"key": "app.request_id", "value": "req_1"}, applied)


if __name__ == "__main__":
    unittest.main()
