import unittest

from gridlens_observability import bind_context, redact_value, structured_record


class ObservabilityTests(unittest.TestCase):
    def test_redacts_account_tokens_and_signed_urls(self):
        self.assertEqual("12***90", redact_value("1234567890"))
        self.assertEqual("[redacted]", redact_value("token=abc"))
        self.assertEqual("[redacted]", redact_value("api_key=abc"))
        self.assertEqual("[redacted]", redact_value("Authorization: Bearer abc"))
        self.assertEqual("[redacted-url]", redact_value("https://example.test/file?X-Amz-Signature=abc"))

    def test_structured_record_includes_safe_correlation_context(self):
        bind_context(
            request_id="req_1",
            correlation_id="corr_1",
            tenant_id="tenant_a",
            actor_id="user_a",
            service="api",
            job_id="job_1",
            token="secret",
        )
        record = structured_record("done", outcome="ok")
        self.assertEqual("req_1", record["request_id"])
        self.assertEqual("tenant_a", record["tenant_id"])
        self.assertEqual("***", record["token"])

    def test_structured_record_redacts_common_secret_field_variants(self):
        record = structured_record(
            "done",
            api_key="secret",
            access_token="secret",
            authorization="Bearer secret",
            credential_id="secret",
            outcome="ok",
        )
        self.assertEqual("***", record["api_key"])
        self.assertEqual("***", record["access_token"])
        self.assertEqual("***", record["authorization"])
        self.assertEqual("***", record["credential_id"])
        self.assertEqual("ok", record["outcome"])


if __name__ == "__main__":
    unittest.main()
