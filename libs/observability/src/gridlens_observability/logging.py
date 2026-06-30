import json
import logging
from datetime import UTC, datetime
from typing import Any

from .context import bind_context, clear_context, current_context_fields, reset_context
from .redaction import redact_field, redact_value


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


def structured_record(message: str, **fields: Any) -> dict[str, Any]:
    record = current_context_fields()
    record.update({key: redact_field(key, value) for key, value in fields.items()})
    record["message"] = message
    return record


__all__ = [
    "JsonFormatter",
    "bind_context",
    "clear_context",
    "configure_json_logging",
    "redact_value",
    "reset_context",
    "structured_record",
]
