import logging
import unittest
from io import StringIO
from json import loads
from unittest.mock import patch

from gridlens_observability import (
    InMemoryMetricExporter,
    InMemoryTraceExporter,
    bind_context,
    clear_context,
    configure_json_logging,
    configure_otel_logging,
    counter,
    current_context,
    extract_trace_context,
    gauge,
    histogram,
    inject_trace_context,
    is_gridlens_json_handler,
    is_gridlens_otel_handler,
    log_extra,
    redact_value,
    reset_context,
    set_metric_exporter,
    set_trace_exporter,
    settings_from_env,
    start_span,
    structured_record,
)
from opentelemetry.instrumentation.logging.handler import LoggingHandler


class ObservabilityTests(unittest.TestCase):
    def tearDown(self):
        clear_context()
        set_metric_exporter(InMemoryMetricExporter())
        set_trace_exporter(InMemoryTraceExporter())
        logging.getLogger().handlers = [
            handler
            for handler in logging.getLogger().handlers
            if not is_gridlens_json_handler(handler)
            and not is_gridlens_otel_handler(handler)
        ]

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
        record = structured_record("done")
        self.assertEqual("info", record["level"])
        self.assertEqual("done", record["message"])
        self.assertEqual("test_context_can_be_cleared_or_reset", record["source_function"])

    def test_structured_record_redacts_common_secret_field_variants(self):
        clear_context()
        record = structured_record(
            "done",
            level="warning",
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
        self.assertEqual("warning", record["level"])
        self.assertEqual("ok", record["outcome"])

    def test_structured_record_redacts_domain_identifier_fields(self):
        clear_context()
        record = structured_record(
            "done",
            account_id="acct_123",
            account_number="1234567890",
            meter_id="meter-abc-123",
            participant_id="participant-42",
            route="/health",
        )
        self.assertEqual("***", record["account_id"])
        self.assertEqual("******7890", record["account_number"])
        self.assertEqual("***", record["meter_id"])
        self.assertEqual("***", record["participant_id"])
        self.assertEqual("/health", record["route"])

    def test_log_extra_merges_context_and_redacts_fields_for_stdlib_logging(self):
        clear_context()
        bind_context(request_id="req_1", tenant_id="tenant_a")
        logger = logging.getLogger("gridlens.test")

        with self.assertLogs("gridlens.test", level="INFO") as captured:
            logger.info("event_completed", **log_extra(api_key="secret", outcome="ok"))

        record = captured.records[0]
        self.assertEqual("event_completed", record.getMessage())
        self.assertEqual("req_1", record.__dict__["request_id"])
        self.assertEqual("tenant_a", record.__dict__["tenant_id"])
        self.assertEqual("***", record.__dict__["api_key"])
        self.assertEqual("ok", record.__dict__["outcome"])

    def test_configure_otel_logging_installs_standard_logging_handler(self):
        configure_otel_logging(endpoint="http://otel-collector:4318", service_name="test-service")

        otel_handlers = [
            handler
            for handler in logging.getLogger().handlers
            if is_gridlens_otel_handler(handler)
        ]
        self.assertEqual(1, len(otel_handlers))
        self.assertIsInstance(otel_handlers[0], LoggingHandler)

    def test_configure_json_logging_structures_uvicorn_access_logs(self):
        stream = StringIO()
        with patch("sys.stderr", stream):
            configure_json_logging()
            logger = logging.getLogger("uvicorn.access")
            logger.info(
                '%s - "%s %s HTTP/%s" %d',
                "127.0.0.1:1234",
                "GET",
                "/health",
                "1.1",
                200,
            )

        payload = loads(stream.getvalue())
        self.assertEqual("http_access", payload["message"])
        self.assertEqual("info", payload["level"])
        self.assertEqual("GET", payload["method"])
        self.assertEqual("/health", payload["route"])
        self.assertEqual(200, payload["status_code"])
        self.assertEqual("uvicorn.access", payload["logger"])

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

    def test_metrics_and_spans_redact_domain_identifier_attributes(self):
        clear_context()
        metrics = InMemoryMetricExporter()
        traces = InMemoryTraceExporter()
        set_metric_exporter(metrics)
        set_trace_exporter(traces)

        counter(
            "gridlens.requests.total",
            meter_id="meter-abc-123",
            participant_id="participant-42",
            route="/health",
        )
        with start_span(
            "service.lookup",
            account_id="acct_123",
            account_number="1234567890",
            meter_number="meter-abc-123",
        ):
            pass

        metric_attributes = metrics.records()[0].attributes
        self.assertEqual("***", metric_attributes["meter_id"])
        self.assertEqual("***", metric_attributes["participant_id"])
        self.assertEqual("/health", metric_attributes["route"])

        span_attributes = traces.records()[0].attributes
        self.assertEqual("***", span_attributes["account_id"])
        self.assertEqual("******7890", span_attributes["account_number"])
        self.assertEqual("***", span_attributes["meter_number"])

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
        self.assertEqual("otlp", production.metrics_exporter)
        self.assertEqual("stdout", production.log_exporter)
        self.assertEqual("otlp", production.traces_exporter)
        self.assertEqual("http://localhost:4318", production.otlp_endpoint)

        test = settings_from_env({"OBSERVABILITY_MODE": "test"})
        self.assertEqual("noop", test.metrics_exporter)
        self.assertEqual("stdout", test.log_exporter)
        self.assertEqual("noop", test.traces_exporter)


if __name__ == "__main__":
    unittest.main()
