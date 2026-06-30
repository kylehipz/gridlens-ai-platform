import unittest

from gridlens_observability import (
    InMemoryMetricExporter,
    InMemoryTraceExporter,
    bind_context,
    clear_context,
    counter,
    current_context,
    extract_trace_context,
    gauge,
    histogram,
    inject_trace_context,
    redact_value,
    reset_context,
    set_metric_exporter,
    set_trace_exporter,
    settings_from_env,
    start_span,
    structured_record,
)


class ObservabilityTests(unittest.TestCase):
    def tearDown(self):
        clear_context()
        set_metric_exporter(InMemoryMetricExporter())
        set_trace_exporter(InMemoryTraceExporter())

    def test_redacts_account_tokens_and_signed_urls(self):
        self.assertEqual("******7890", redact_value("1234567890"))
        self.assertEqual("[redacted]", redact_value("token=abc"))
        self.assertEqual("[redacted]", redact_value("api_key=abc"))
        self.assertEqual("[redacted]", redact_value("Authorization: Bearer abc"))
        self.assertEqual("[redacted-url]", redact_value("https://example.test/file?X-Amz-Signature=abc"))

    def test_structured_record_includes_safe_correlation_context(self):
        clear_context()
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

    def test_context_can_be_cleared_or_reset(self):
        clear_context()
        token = bind_context(request_id="req_1")
        bind_context(request_id="req_2")
        self.assertEqual("req_2", current_context().request_id)

        reset_context(token)
        self.assertIsNone(current_context().request_id)

        bind_context(request_id="req_3")
        clear_context()
        self.assertEqual({"message": "done"}, structured_record("done"))

    def test_structured_record_redacts_common_secret_field_variants(self):
        clear_context()
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

    def test_metric_records_include_safe_context_and_low_cardinality_attributes(self):
        clear_context()
        exporter = InMemoryMetricExporter()
        set_metric_exporter(exporter)
        bind_context(request_id="req_1", tenant_id="tenant_a", prompt="tell me secrets")

        counter("gridlens.requests.total", route="/health", status_code=200)
        histogram("gridlens.request.duration", 12.5, unit="ms", account_number="1234567890")
        gauge("gridlens.queue.depth", 3, queue="jobs")

        records = exporter.records()
        self.assertEqual(["counter", "histogram", "gauge"], [record.kind for record in records])
        self.assertEqual("tenant_a", records[0].attributes["tenant_id"])
        self.assertEqual("***", records[0].attributes["prompt"])
        self.assertEqual("******7890", records[1].attributes["account_number"])

    def test_trace_spans_propagate_context_and_capture_errors(self):
        clear_context()
        exporter = InMemoryTraceExporter()
        set_trace_exporter(exporter)
        bind_context(request_id="req_1")

        with start_span("gateway.request", route="/health") as gateway:
            carrier = inject_trace_context({"request_id": "req_1"})
            parent = extract_trace_context(carrier)
            self.assertEqual(gateway.trace_id, parent.trace_id if parent else None)
            with start_span("worker.consume", parent=parent, job_id="job_1"):
                pass

        records = exporter.records()
        self.assertEqual(["worker.consume", "gateway.request"], [record.name for record in records])
        self.assertEqual(records[1].trace_id, records[0].trace_id)
        self.assertEqual(records[1].span_id, records[0].parent_span_id)
        self.assertEqual("req_1", records[0].attributes["request_id"])

    def test_trace_span_records_safe_error_status(self):
        clear_context()
        exporter = InMemoryTraceExporter()
        set_trace_exporter(exporter)

        with self.assertRaises(RuntimeError):
            with start_span("service.error", api_key="secret"):
                raise RuntimeError("boom")

        record = exporter.records()[0]
        self.assertEqual("error", record.status)
        self.assertEqual("RuntimeError", record.error_type)
        self.assertEqual("***", record.attributes["api_key"])

    def test_settings_select_exporters_by_environment(self):
        local = settings_from_env({"OBSERVABILITY_MODE": "local"})
        self.assertEqual("prometheus", local.metrics_exporter)
        self.assertEqual("loki", local.log_exporter)
        self.assertEqual("tempo", local.traces_exporter)

        production = settings_from_env({"OBSERVABILITY_MODE": "production"})
        self.assertEqual("cloudwatch", production.metrics_exporter)
        self.assertEqual("cloudwatch-logs", production.log_exporter)
        self.assertEqual("xray", production.traces_exporter)

        test = settings_from_env({"OBSERVABILITY_MODE": "test"})
        self.assertEqual("noop", test.metrics_exporter)
        self.assertEqual("stdout", test.log_exporter)
        self.assertEqual("noop", test.traces_exporter)


if __name__ == "__main__":
    unittest.main()
