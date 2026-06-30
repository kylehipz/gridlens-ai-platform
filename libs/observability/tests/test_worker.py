import logging

import pytest
from gridlens_observability import (
    InMemoryMetricExporter,
    InMemoryTraceExporter,
    WorkerMessageContext,
    observe_worker_job,
    set_metric_exporter,
    set_trace_exporter,
)


def test_worker_job_success_records_logs_metrics_and_consumer_span(caplog) -> None:
    metrics = InMemoryMetricExporter()
    traces = InMemoryTraceExporter()
    set_metric_exporter(metrics)
    set_trace_exporter(traces)

    with caplog.at_level(logging.INFO, logger="gridlens.data-operations-service.worker"):
        with observe_worker_job(
            service_name="data-operations-service",
            worker_name="worker",
            job_id="job_1",
            tenant_id="tenant_a",
            correlation_id="corr_1",
            request_id="req_1",
            trace_id="trace_1",
            span_id="span_1",
        ) as context:
            assert context.job_id == "job_1"

    records = [record for record in caplog.records if record.name == "gridlens.data-operations-service.worker"]
    assert [record.getMessage() for record in records] == [
        "worker_job_started",
        "worker_job_succeeded",
    ]
    assert records[0].job_id == "job_1"
    assert records[0].tenant_id == "tenant_a"
    assert records[0].request_id == "req_1"
    assert metrics.records()[0].name == "gridlens.worker.job.duration"
    assert metrics.records()[0].attributes["status"] == "success"
    assert traces.records()[0].name == "worker.consume"
    assert traces.records()[0].trace_id == "trace_1"
    assert traces.records()[0].parent_span_id == "span_1"


def test_worker_job_failure_logs_safe_fields_and_error_metrics(caplog) -> None:
    metrics = InMemoryMetricExporter()
    traces = InMemoryTraceExporter()
    set_metric_exporter(metrics)
    set_trace_exporter(traces)

    with pytest.raises(RuntimeError):
        with caplog.at_level(logging.INFO, logger="gridlens.data-operations-service.worker"):
            with observe_worker_job(
                service_name="data-operations-service",
                worker_name="worker",
                job_id="job_1",
                tenant_id="tenant_a",
                correlation_id="corr_1",
                request_id="req_1",
                trace_id="trace_1",
                span_id="span_1",
                failure_category="validation_error",
                user_safe_failure_message="The job input is invalid.",
            ):
                raise RuntimeError("raw secret token=abc")

    failure_record = next(
        record for record in caplog.records if record.getMessage() == "worker_job_failed"
    )
    assert failure_record.job_id == "job_1"
    assert failure_record.tenant_id == "tenant_a"
    assert failure_record.failure_category == "validation_error"
    assert failure_record.user_message == "The job input is invalid."
    assert failure_record.error_function == "test_worker_job_failure_logs_safe_fields_and_error_metrics"
    assert failure_record.error_module_path == "test_worker"
    assert failure_record.error_file_path.endswith("test_worker.py")
    assert isinstance(failure_record.error_line_no, int)
    assert failure_record.levelname == "ERROR"
    assert "raw secret token=abc" not in str(failure_record.__dict__)
    assert metrics.records()[0].name == "gridlens.worker.job.errors"
    assert metrics.records()[0].attributes["failure_category"] == "validation_error"
    assert metrics.records()[1].attributes["status"] == "failure"
    assert traces.records()[0].status == "error"


def test_worker_message_context_rebinds_queue_attributes() -> None:
    context = WorkerMessageContext.from_attributes(
        {
            "tenant_id": "tenant_a",
            "correlation_id": "corr_1",
            "request_id": "req_1",
            "trace_id": "trace_1",
            "span_id": "span_1",
        },
        job_id="job_1",
    )

    assert context.tenant_id == "tenant_a"
    assert context.job_id == "job_1"
    trace_context = context.trace_context()
    assert trace_context is not None
    assert trace_context.trace_id == "trace_1"
