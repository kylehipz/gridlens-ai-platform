from collections.abc import Callable, Iterable
from dataclasses import dataclass, field
from threading import Lock
from typing import Protocol

from opentelemetry.exporter.otlp.proto.http.metric_exporter import OTLPMetricExporter
from opentelemetry.metrics import (
    CallbackOptions,
    Counter,
    Histogram,
    ObservableGauge,
    Observation,
)
from opentelemetry.sdk.metrics import MeterProvider
from opentelemetry.sdk.metrics.export import PeriodicExportingMetricReader
from opentelemetry.sdk.resources import Resource

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


class OtlpMetricExporter:
    def __init__(self, endpoint: str, *, service_name: str) -> None:
        reader = PeriodicExportingMetricReader(
            OTLPMetricExporter(endpoint=f"{endpoint.rstrip('/')}/v1/metrics", timeout=1),
            export_interval_millis=1000,
            export_timeout_millis=1000,
        )
        self._provider = MeterProvider(
            metric_readers=[reader],
            resource=Resource.create({"service.name": service_name}),
        )
        self._meter = self._provider.get_meter("gridlens_observability")
        self._counters: dict[tuple[str, str], Counter] = {}
        self._histograms: dict[tuple[str, str], Histogram] = {}
        self._gauges: dict[tuple[str, str], ObservableGauge] = {}
        self._gauge_values: dict[
            tuple[str, str], dict[tuple[tuple[str, str | int | float | bool], ...], MetricValue]
        ] = {}
        self._lock = Lock()

    def emit(self, record: MetricRecord) -> None:
        unit = record.unit or ""
        key = (record.name, unit)
        if record.kind == "counter":
            self._counter(key).add(record.value, record.attributes)
        elif record.kind == "histogram":
            self._histogram(key).record(record.value, record.attributes)
        elif record.kind == "gauge":
            self._record_gauge(key, record.value, record.attributes)

    def _counter(self, key: tuple[str, str]) -> Counter:
        with self._lock:
            instrument = self._counters.get(key)
            if instrument is None:
                name, unit = key
                instrument = self._meter.create_counter(name, unit=unit)
                self._counters[key] = instrument
            return instrument

    def _histogram(self, key: tuple[str, str]) -> Histogram:
        with self._lock:
            instrument = self._histograms.get(key)
            if instrument is None:
                name, unit = key
                instrument = self._meter.create_histogram(name, unit=unit)
                self._histograms[key] = instrument
            return instrument

    def _record_gauge(
        self,
        key: tuple[str, str],
        value: MetricValue,
        attributes: dict[str, str | int | float | bool],
    ) -> None:
        with self._lock:
            if key not in self._gauges:
                name, unit = key
                self._gauge_values[key] = {}
                self._gauges[key] = self._meter.create_observable_gauge(
                    name,
                    callbacks=[self._gauge_callback(key)],
                    unit=unit,
                )
            self._gauge_values[key][_attribute_key(attributes)] = value

    def _gauge_callback(
        self, key: tuple[str, str]
    ) -> Callable[[CallbackOptions], Iterable[Observation]]:
        def observe(_options: CallbackOptions) -> Iterable[Observation]:
            with self._lock:
                values = list(self._gauge_values.get(key, {}).items())
            for attributes, value in values:
                yield Observation(value, dict(attributes))

        return observe


_metric_exporter: MetricExporter = NoopMetricExporter()


def set_metric_exporter(exporter: MetricExporter) -> None:
    global _metric_exporter
    _metric_exporter = exporter


def configure_otel_metrics(*, endpoint: str, service_name: str) -> None:
    set_metric_exporter(OtlpMetricExporter(endpoint, service_name=service_name))


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


def _attribute_key(
    attributes: dict[str, str | int | float | bool]
) -> tuple[tuple[str, str | int | float | bool], ...]:
    return tuple(sorted(attributes.items()))
