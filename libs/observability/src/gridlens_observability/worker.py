import logging
from contextlib import contextmanager
from dataclasses import dataclass
from time import perf_counter
from typing import Iterator

from .context import bind_context, clear_context
from .logging import exception_source_fields, log_extra
from .metrics import counter, histogram
from .tracing import TraceContext, extract_trace_context, start_span


@dataclass(frozen=True)
class WorkerMessageContext:
    tenant_id: str
    correlation_id: str
    request_id: str | None = None
    trace_id: str | None = None
    span_id: str | None = None
    job_id: str | None = None

    @classmethod
    def from_attributes(cls, attributes: dict[str, str], *, job_id: str | None = None) -> "WorkerMessageContext":
        return cls(
            tenant_id=attributes["tenant_id"],
            correlation_id=attributes["correlation_id"],
            request_id=attributes.get("request_id"),
            trace_id=attributes.get("trace_id"),
            span_id=attributes.get("span_id"),
            job_id=job_id or attributes.get("job_id"),
        )

    def trace_context(self) -> TraceContext | None:
        return extract_trace_context(
            {
                "trace_id": self.trace_id or "",
                "span_id": self.span_id or "",
            }
        )


@contextmanager
def observe_worker_job(
    *,
    service_name: str,
    worker_name: str,
    job_id: str,
    tenant_id: str,
    correlation_id: str,
    request_id: str | None = None,
    trace_id: str | None = None,
    span_id: str | None = None,
    failure_category: str = "worker_error",
    user_safe_failure_message: str = "Worker job failed.",
) -> Iterator[WorkerMessageContext]:
    logger = logging.getLogger(f"gridlens.{service_name}.{worker_name}")
    message_context = WorkerMessageContext(
        tenant_id=tenant_id,
        correlation_id=correlation_id,
        request_id=request_id,
        trace_id=trace_id,
        span_id=span_id,
        job_id=job_id,
    )
    bind_context(
        request_id=request_id,
        correlation_id=correlation_id,
        trace_id=trace_id,
        span_id=span_id,
        tenant_id=tenant_id,
        service=service_name,
        worker=worker_name,
        job_id=job_id,
    )
    started_at = perf_counter()
    status = "success"
    active_span: TraceContext | None = None
    try:
        logger.info("worker_job_started", **log_extra())
        with start_span("worker.consume", parent=message_context.trace_context(), worker=worker_name) as span:
            active_span = span
            yield message_context
        if active_span:
            bind_context(trace_id=active_span.trace_id, span_id=active_span.span_id)
        logger.info("worker_job_succeeded", **log_extra())
    except Exception as exc:
        status = "failure"
        if active_span:
            bind_context(trace_id=active_span.trace_id, span_id=active_span.span_id)
        counter(
            "gridlens.worker.job.errors",
            service=service_name,
            worker=worker_name,
            failure_category=failure_category,
            error_type=exc.__class__.__name__,
        )
        logger.error(
            "worker_job_failed",
            **log_extra(
                failure_category=failure_category,
                user_message=user_safe_failure_message,
                error_type=exc.__class__.__name__,
                **exception_source_fields(exc.__traceback__),
            ),
        )
        raise
    finally:
        duration_ms = (perf_counter() - started_at) * 1000
        histogram(
            "gridlens.worker.job.duration",
            duration_ms,
            unit="ms",
            service=service_name,
            worker=worker_name,
            status=status,
        )
        clear_context()
