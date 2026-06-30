from contextlib import contextmanager
from dataclasses import dataclass, field
from time import perf_counter
from typing import Iterator, Protocol
from uuid import uuid4

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


class TraceExporter(Protocol):
    def emit(self, record: SpanRecord) -> None:
        ...


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


_trace_exporter: TraceExporter = NoopTraceExporter()


def set_trace_exporter(exporter: TraceExporter) -> None:
    global _trace_exporter
    _trace_exporter = exporter


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
    span_id = _new_id()
    token = bind_context(trace_id=trace_id, span_id=span_id)
    started_at = perf_counter()
    status = "ok"
    error_type: str | None = None
    try:
        yield TraceContext(trace_id=trace_id, span_id=span_id, parent_span_id=parent_span_id)
    except Exception as exc:
        status = "error"
        error_type = exc.__class__.__name__
        raise
    finally:
        duration_ms = (perf_counter() - started_at) * 1000
        merged = current_context_fields()
        merged.update(attributes)
        _trace_exporter.emit(
            SpanRecord(
                name=name,
                trace_id=trace_id,
                span_id=span_id,
                parent_span_id=parent_span_id,
                attributes=safe_attributes(merged),
                duration_ms=duration_ms,
                status=status,
                error_type=error_type,
            )
        )
        reset_context(token)


def _new_id() -> str:
    return uuid4().hex
