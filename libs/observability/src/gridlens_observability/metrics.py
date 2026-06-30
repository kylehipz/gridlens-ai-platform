import json
from dataclasses import dataclass, field
from threading import Lock
from time import time_ns
from typing import Any, Protocol
from urllib import request

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
        self.endpoint = endpoint.rstrip("/")
        self.service_name = service_name

    def emit(self, record: MetricRecord) -> None:
        payload = {
            "resourceMetrics": [
                {
                    "resource": {
                        "attributes": [_string_attribute("service.name", self.service_name)]
                    },
                    "scopeMetrics": [
                        {
                            "scope": {"name": "gridlens_observability"},
                            "metrics": [_metric_payload(record)],
                        }
                    ],
                }
            ]
        }
        _post_json(f"{self.endpoint}/v1/metrics", payload)


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


def _metric_payload(record: MetricRecord) -> dict[str, object]:
    data_point = {
        "attributes": _attributes(record.attributes),
        "timeUnixNano": str(time_ns()),
    }
    if record.kind == "histogram":
        data_point.update({"count": "1", "sum": float(record.value)})
        return {
            "name": record.name,
            "unit": record.unit or "",
            "histogram": {"aggregationTemporality": 2, "dataPoints": [data_point]},
        }
    data_point["asDouble"] = float(record.value)
    if record.kind == "counter":
        return {
            "name": record.name,
            "unit": record.unit or "",
            "sum": {
                "aggregationTemporality": 2,
                "isMonotonic": True,
                "dataPoints": [data_point],
            },
        }
    return {
        "name": record.name,
        "unit": record.unit or "",
        "gauge": {"dataPoints": [data_point]},
    }


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
    req = request.Request(url, data=body, headers={"Content-Type": "application/json"}, method="POST")
    try:
        request.urlopen(req, timeout=0.25).close()
    except OSError:
        return None
