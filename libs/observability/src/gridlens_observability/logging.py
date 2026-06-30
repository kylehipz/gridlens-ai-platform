import json
import logging
from datetime import UTC, datetime
from time import time_ns
from typing import Any, Protocol
from urllib import request

from .context import bind_context, clear_context, current_context_fields, reset_context
from .redaction import redact_field, redact_value


class LogExporter(Protocol):
    def emit(self, record: dict[str, Any]) -> None:
        ...


class NoopLogExporter:
    def emit(self, record: dict[str, Any]) -> None:
        return None


class InMemoryLogExporter:
    def __init__(self) -> None:
        self.records: list[dict[str, Any]] = []

    def emit(self, record: dict[str, Any]) -> None:
        self.records.append(dict(record))


class OtlpLogExporter:
    def __init__(self, endpoint: str, *, service_name: str) -> None:
        self.endpoint = endpoint.rstrip("/")
        self.service_name = service_name

    def emit(self, record: dict[str, Any]) -> None:
        payload = {
            "resourceLogs": [
                {
                    "resource": {
                        "attributes": [
                            {"key": "service.name", "value": {"stringValue": self.service_name}}
                        ]
                    },
                    "scopeLogs": [
                        {
                            "scope": {"name": "gridlens_observability"},
                            "logRecords": [
                                {
                                    "timeUnixNano": str(time_ns()),
                                    "severityText": str(record.get("level", "INFO")).upper(),
                                    "body": {"stringValue": record.get("message", "")},
                                    "attributes": [
                                        {
                                            "key": key,
                                            "value": {"stringValue": str(value)},
                                        }
                                        for key, value in record.items()
                                        if value is not None
                                    ],
                                }
                            ],
                        }
                    ],
                }
            ]
        }
        body = json.dumps(payload).encode("utf-8")
        req = request.Request(
            f"{self.endpoint}/v1/logs",
            data=body,
            headers={"Content-Type": "application/json"},
            method="POST",
        )
        try:
            request.urlopen(req, timeout=0.25).close()
        except OSError:
            return None


_log_exporter: LogExporter = NoopLogExporter()


def set_log_exporter(exporter: LogExporter) -> None:
    global _log_exporter
    _log_exporter = exporter


class JsonFormatter(logging.Formatter):
    def format(self, record: logging.LogRecord) -> str:
        payload = structured_record(
            record.getMessage(),
            level=record.levelname.lower(),
            logger=record.name,
            timestamp=datetime.fromtimestamp(record.created, UTC).isoformat(),
        )
        if record.exc_info and record.exc_info[0]:
            payload["exception_type"] = record.exc_info[0].__name__
        return json.dumps(payload, sort_keys=True, separators=(",", ":"))


def configure_json_logging(level: int = logging.INFO) -> None:
    handler = logging.StreamHandler()
    handler.setFormatter(JsonFormatter())
    root = logging.getLogger()
    root.handlers = [handler]
    root.setLevel(level)


def json_log_record(message: str, **fields: Any) -> str:
    record = structured_record(message, **fields)
    _log_exporter.emit(record)
    return json.dumps(record, sort_keys=True, separators=(",", ":"))


def structured_record(message: str, **fields: Any) -> dict[str, Any]:
    record = current_context_fields()
    record.update({key: redact_field(key, value) for key, value in fields.items()})
    record["message"] = message
    return record


__all__ = [
    "JsonFormatter",
    "InMemoryLogExporter",
    "bind_context",
    "clear_context",
    "configure_json_logging",
    "json_log_record",
    "set_log_exporter",
    "redact_value",
    "reset_context",
    "structured_record",
]
