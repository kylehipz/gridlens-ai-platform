from dataclasses import dataclass, field
from threading import Lock
from typing import Protocol
from urllib.parse import quote

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


class PrometheusMetricExporter(InMemoryMetricExporter):
    def render(self) -> str:
        counters: dict[tuple[str, tuple[tuple[str, str], ...]], float] = {}
        histograms: dict[tuple[str, tuple[tuple[str, str], ...]], tuple[int, float]] = {}
        gauges: dict[tuple[str, tuple[tuple[str, str], ...]], float] = {}

        for record in self.records():
            key = (_prometheus_name(record.name), _labels(record.attributes))
            value = float(record.value)
            if record.kind == "counter":
                counters[key] = counters.get(key, 0.0) + value
            elif record.kind == "histogram":
                count, total = histograms.get(key, (0, 0.0))
                histograms[key] = (count + 1, total + value)
            elif record.kind == "gauge":
                gauges[key] = value

        lines = [
            "# HELP gridlens_metrics GridLens application metrics.",
            "# TYPE gridlens_metrics untyped",
        ]
        for (name, labels), value in sorted(counters.items()):
            lines.append(f"{name}_total{_label_text(labels)} {value:g}")
        for (name, labels), (count, total) in sorted(histograms.items()):
            lines.append(f"{name}_count{_label_text(labels)} {count}")
            lines.append(f"{name}_sum{_label_text(labels)} {total:g}")
        for (name, labels), value in sorted(gauges.items()):
            lines.append(f"{name}{_label_text(labels)} {value:g}")
        return "\n".join(lines) + "\n"


_metric_exporter: MetricExporter = NoopMetricExporter()


def set_metric_exporter(exporter: MetricExporter) -> None:
    global _metric_exporter
    _metric_exporter = exporter


def prometheus_metrics_text() -> str:
    if isinstance(_metric_exporter, PrometheusMetricExporter):
        return _metric_exporter.render()
    return "# HELP gridlens_metrics GridLens application metrics.\n# TYPE gridlens_metrics untyped\n"


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


def _prometheus_name(name: str) -> str:
    return "".join(character if character.isalnum() else "_" for character in name)


def _labels(attributes: dict[str, str | int | float | bool]) -> tuple[tuple[str, str], ...]:
    allowed = {"service", "worker", "route", "method", "status_code", "failure_category"}
    return tuple(sorted((key, str(value)) for key, value in attributes.items() if key in allowed))


def _label_text(labels: tuple[tuple[str, str], ...]) -> str:
    if not labels:
        return ""
    body = ",".join(f'{key}="{quote(value, safe="/:-_")}"' for key, value in labels)
    return f"{{{body}}}"
