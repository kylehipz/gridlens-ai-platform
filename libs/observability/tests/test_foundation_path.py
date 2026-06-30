import logging

from gridlens_contracts.audit import AuditAction, AuditContext, AuditEvent
from gridlens_contracts.tenant_context import ActorContext
from gridlens_events import build_event, queue_message_attributes
from gridlens_observability import (
    InMemoryMetricExporter,
    InMemoryTraceExporter,
    bind_context,
    current_context,
    log_extra,
    observe_worker_job,
    set_metric_exporter,
    set_trace_exporter,
    start_span,
)


def test_synthetic_gateway_service_worker_audit_path_preserves_safe_context(caplog) -> None:
    metrics = InMemoryMetricExporter()
    traces = InMemoryTraceExporter()
    set_metric_exporter(metrics)
    set_trace_exporter(traces)
    logger = logging.getLogger("gridlens.synthetic")

    with caplog.at_level(logging.INFO, logger="gridlens"):
        bind_context(
            request_id="req_1",
            correlation_id="corr_1",
            tenant_id="tenant_a",
            service="gateway",
        )
        with start_span("gateway.request") as gateway_span:
            logger.info("gateway_received", **log_extra(account_number="1234567890"))
            context = current_context()
            event = build_event(
                event_type="generic.workflow.requested",
                tenant_id="tenant_a",
                correlation_id="corr_1",
                request_id=context.request_id,
                trace_id=context.trace_id,
                span_id=context.span_id,
                actor=ActorContext.system("gateway"),
                source_resource_ids={"job_id": "job_1"},
                payload={"safe": True},
            )

        attributes = queue_message_attributes(event)
        with observe_worker_job(
            service_name="data-operations-service",
            worker_name="worker",
            job_id="job_1",
            tenant_id=attributes["tenant_id"],
            correlation_id=attributes["correlation_id"],
            request_id=attributes["request_id"],
            trace_id=attributes["trace_id"],
            span_id=attributes["span_id"],
        ):
            audit = AuditEvent(
                action=AuditAction.JOB_RETRIED.value,
                tenant_id="tenant_a",
                actor_id="worker",
                target_type="job",
                target_id="job_1",
                context=AuditContext(
                    request_id=attributes["request_id"],
                    correlation_id=attributes["correlation_id"],
                    trace_id=attributes["trace_id"],
                    span_id=attributes["span_id"],
                ),
            ).to_dict()
            logger.info("audit_recorded", **log_extra(audit_context=audit["context"]))

    records = [record for record in caplog.records if record.name.startswith("gridlens")]
    assert {record.correlation_id for record in records} == {"corr_1"}
    assert {record.request_id for record in records} == {"req_1"}
    assert records[0].account_number == "******7890"
    assert "1234567890" not in str([record.__dict__ for record in records])

    assert attributes["request_id"] == "req_1"
    assert attributes["correlation_id"] == "corr_1"
    assert attributes["trace_id"] == gateway_span.trace_id
    assert audit["context"]["trace_id"] == gateway_span.trace_id

    duration_metric = next(
        record for record in metrics.records() if record.name == "gridlens.worker.job.duration"
    )
    assert duration_metric.attributes["request_id"] == "req_1"
    assert duration_metric.attributes["correlation_id"] == "corr_1"
    assert duration_metric.attributes["trace_id"] == gateway_span.trace_id

    span_names = [record.name for record in traces.records()]
    assert span_names == ["gateway.request", "worker.consume"]
    assert {record.trace_id for record in traces.records()} == {gateway_span.trace_id}
