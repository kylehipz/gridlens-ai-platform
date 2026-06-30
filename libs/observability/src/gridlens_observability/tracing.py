import json
from contextlib import contextmanager
from dataclasses import dataclass, field
from time import perf_counter, time_ns
from typing import Any, Iterator, Protocol
from urllib import request
from uuid import uuid4

from opentelemetry import trace
from opentelemetry.context import Context
from opentelemetry.exporter.otlp.proto.http.trace_exporter import OTLPSpanExporter
from opentelemetry.sdk.resources import Resource
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor
from opentelemetry.trace import (
    INVALID_SPAN_CONTEXT,
    NonRecordingSpan,
    Span,
    SpanContext,
    SpanKind,
    Status,
    StatusCode,
    TraceFlags,
    TraceState,
    set_span_in_context,
)

from .context import bind_context, current_context, current_context_fields, reset_context
from .redaction import safe_attributes


@dataclass(frozen=True)
class TraceContext:
    trace_id: str
    span_id: str
    parent_span_id: str | None = None

    def to_headers(self) -> dict[str, str]:
        headers = {"trace_id": self.trace_id, "span_id": self.span_id}
        if self.parent_span_id:
            headers["parent_span_id"] = self.parent_span_id
        return headers


@dataclass(frozen=True)
class SpanRecord:
    name: str
    trace_id: str
    span_id: str
    parent_span_id: str | None
    attributes: dict[str, str | int | float | bool] = field(default_factory=dict)
    duration_ms: float = 0.0
    status: str = "ok"
    error_type: str | None = None
    end_time_unix_nano: int = 0


class TraceExporter(Protocol):
    def emit(self, record: SpanRecord) -> None: ...


class NoopTraceExporter:
    def emit(self, record: SpanRecord) -> None:
        return None


class InMemoryTraceExporter:
    def __init__(self) -> None:
        self._records: list[SpanRecord] = []

    def emit(self, record: SpanRecord) -> None:
        self._records.append(record)

    def records(self) -> list[SpanRecord]:
        return list(self._records)

    def clear(self) -> None:
        self._records.clear()


class OtlpTraceExporter:
    def __init__(self, endpoint: str, *, service_name: str) -> None:
        self.endpoint = endpoint.rstrip("/")
        self.service_name = service_name

    def emit(self, record: SpanRecord) -> None:
        payload = {
            "resourceSpans": [
                {
                    "resource": {
                        "attributes": [_string_attribute("service.name", self.service_name)]
                    },
                    "scopeSpans": [
                        {
                            "scope": {"name": "gridlens_observability"},
                            "spans": [
                                {
                                    "traceId": record.trace_id,
                                    "spanId": record.span_id,
                                    "parentSpanId": record.parent_span_id or "",
                                    "name": record.name,
                                    "kind": 1,
                                    "startTimeUnixNano": str(
                                        max(
                                            record.end_time_unix_nano
                                            - int(record.duration_ms * 1_000_000),
                                            0,
                                        )
                                    ),
                                    "endTimeUnixNano": str(record.end_time_unix_nano),
                                    "attributes": _attributes(record.attributes),
                                    "status": {"code": 2 if record.status == "error" else 1},
                                }
                            ],
                        }
                    ],
                }
            ]
        }
        _post_json(f"{self.endpoint}/v1/traces", payload)


_trace_exporter: TraceExporter = NoopTraceExporter()
_otel_trace_provider: TracerProvider | None = None


def set_trace_exporter(exporter: TraceExporter) -> None:
    global _trace_exporter
    _trace_exporter = exporter


def configure_otel_tracing(*, endpoint: str, service_name: str) -> None:
    global _otel_trace_provider
    provider = TracerProvider(
        resource=Resource.create({"service.name": service_name}),
    )
    provider.add_span_processor(
        BatchSpanProcessor(
            OTLPSpanExporter(endpoint=f"{endpoint.rstrip('/')}/v1/traces"),
            schedule_delay_millis=250,
            export_timeout_millis=1000,
        )
    )
    if _otel_trace_provider is None:
        trace.set_tracer_provider(provider)
    _otel_trace_provider = provider


def extract_trace_context(carrier: dict[str, str] | None) -> TraceContext | None:
    if not carrier:
        return None
    trace_id = carrier.get("trace_id") or carrier.get("x-trace-id")
    span_id = carrier.get("span_id") or carrier.get("x-span-id")
    parent_span_id = carrier.get("parent_span_id") or carrier.get("x-parent-span-id")
    if not trace_id or not span_id:
        return None
    return TraceContext(trace_id=trace_id, span_id=span_id, parent_span_id=parent_span_id)


def inject_trace_context(carrier: dict[str, str] | None = None) -> dict[str, str]:
    target = dict(carrier or {})
    context = current_context()
    if context.trace_id:
        target["trace_id"] = context.trace_id
    if context.span_id:
        target["span_id"] = context.span_id
    return target


@contextmanager
def start_span(
    name: str,
    *,
    parent: TraceContext | None = None,
    **attributes: object,
) -> Iterator[TraceContext]:
    active = current_context()
    trace_id = parent.trace_id if parent else active.trace_id or _new_id()
    parent_span_id = parent.span_id if parent else active.span_id
    span_id = _new_span_id()
    token = bind_context(trace_id=trace_id, span_id=span_id)
    started_at = perf_counter()
    status = "ok"
    error_type: str | None = None
    tracer = trace.get_tracer("gridlens_observability")
    otel_parent = _otel_parent_context(parent)
    span_kind = SpanKind.SERVER if name == "http.server" else SpanKind.INTERNAL
    try:
        with tracer.start_as_current_span(
            name,
            context=otel_parent,
            kind=span_kind,
        ) as otel_span:
            otel_context = otel_span.get_span_context()
            if otel_context != INVALID_SPAN_CONTEXT:
                trace_id = f"{otel_context.trace_id:032x}"
                span_id = f"{otel_context.span_id:016x}"
                reset_context(token)
                token = bind_context(trace_id=trace_id, span_id=span_id)
            try:
                yield TraceContext(
                    trace_id=trace_id, span_id=span_id, parent_span_id=parent_span_id
                )
            except Exception as exc:
                status = "error"
                error_type = exc.__class__.__name__
                raise
            finally:
                duration_ms = (perf_counter() - started_at) * 1000
                merged = current_context_fields()
                merged.update(attributes)
                safe = safe_attributes(merged)
                _annotate_otel_span(otel_span, safe, status=status, error_type=error_type)
                _trace_exporter.emit(
                    SpanRecord(
                        name=name,
                        trace_id=trace_id,
                        span_id=span_id,
                        parent_span_id=parent_span_id,
                        attributes=safe,
                        duration_ms=duration_ms,
                        status=status,
                        error_type=error_type,
                        end_time_unix_nano=time_ns(),
                    )
                )
    finally:
        reset_context(token)


def _annotate_otel_span(
    span: Span,
    attributes: dict[str, str | int | float | bool],
    *,
    status: str,
    error_type: str | None,
) -> None:
    if not span.is_recording():
        return
    for key, value in attributes.items():
        span.set_attribute(key, value)
    if status == "error":
        span.set_status(Status(StatusCode.ERROR, error_type or "error"))
        if error_type:
            span.set_attribute("error.type", error_type)


def _otel_parent_context(parent: TraceContext | None) -> Context | None:
    if parent is None or not _is_hex(parent.trace_id, 32) or not _is_hex(parent.span_id, 16):
        return None
    return set_span_in_context(
        NonRecordingSpan(
            SpanContext(
                trace_id=int(parent.trace_id, 16),
                span_id=int(parent.span_id, 16),
                is_remote=True,
                trace_flags=TraceFlags(TraceFlags.SAMPLED),
                trace_state=TraceState(),
            )
        )
    )


def _is_hex(value: str, length: int) -> bool:
    if len(value) != length:
        return False
    try:
        int(value, 16)
    except ValueError:
        return False
    return True


def _new_id() -> str:
    return uuid4().hex


def _new_span_id() -> str:
    return uuid4().hex[:16]


def _attributes(attributes: dict[str, str | int | float | bool]) -> list[dict[str, object]]:
    return [_attribute(key, value) for key, value in attributes.items()]


def _attribute(key: str, value: str | int | float | bool) -> dict[str, object]:
    if isinstance(value, bool):
        return {"key": key, "value": {"boolValue": value}}
    if isinstance(value, int):
        return {"key": key, "value": {"intValue": str(value)}}
    if isinstance(value, float):
        return {"key": key, "value": {"doubleValue": value}}
    return _string_attribute(key, value)


def _string_attribute(key: str, value: str) -> dict[str, object]:
    return {"key": key, "value": {"stringValue": value}}


def _post_json(url: str, payload: dict[str, Any]) -> None:
    body = json.dumps(payload).encode("utf-8")
    req = request.Request(
        url, data=body, headers={"Content-Type": "application/json"}, method="POST"
    )
    try:
        request.urlopen(req, timeout=0.25).close()
    except OSError:
        return None
