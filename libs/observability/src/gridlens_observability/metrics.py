from dataclasses import dataclass, field
from threading import Lock
from typing import Protocol

from .context import current_context_fields
from .redaction import safe_attributes

MetricValue = int | float


@dataclass(frozen=True)
class MetricRecord:
    name: str
    value: MetricValue
    kind: str
    unit: str | None = None
    attributes: dict[str, str | int | float | bool] = field(default_factory=dict)


class MetricExporter(Protocol):
    def emit(self, record: MetricRecord) -> None:
        ...


class NoopMetricExporter:
    def emit(self, record: MetricRecord) -> None:
        return None


class InMemoryMetricExporter:
    def __init__(self) -> None:
        self._records: list[MetricRecord] = []
        self._lock = Lock()

    def emit(self, record: MetricRecord) -> None:
        with self._lock:
            self._records.append(record)

    def records(self) -> list[MetricRecord]:
        with self._lock:
            return list(self._records)

    def clear(self) -> None:
        with self._lock:
            self._records.clear()


_metric_exporter: MetricExporter = NoopMetricExporter()


def set_metric_exporter(exporter: MetricExporter) -> None:
    global _metric_exporter
    _metric_exporter = exporter


def counter(name: str, value: MetricValue = 1, **attributes: object) -> MetricRecord:
    return _record_metric(name=name, value=value, kind="counter", unit=None, attributes=attributes)


def histogram(
    name: str, value: MetricValue, unit: str | None = None, **attributes: object
) -> MetricRecord:
    return _record_metric(name=name, value=value, kind="histogram", unit=unit, attributes=attributes)


def gauge(name: str, value: MetricValue, unit: str | None = None, **attributes: object) -> MetricRecord:
    return _record_metric(name=name, value=value, kind="gauge", unit=unit, attributes=attributes)


def _record_metric(
    *,
    name: str,
    value: MetricValue,
    kind: str,
    unit: str | None,
    attributes: dict[str, object],
) -> MetricRecord:
    merged = current_context_fields()
    merged.update(attributes)
    record = MetricRecord(
        name=name,
        value=value,
        kind=kind,
        unit=unit,
        attributes=safe_attributes(merged),
    )
    _metric_exporter.emit(record)
    return record
