import re
from contextvars import ContextVar
from typing import Any

_context: ContextVar[dict[str, Any]] = ContextVar("gridlens_log_context", default={})


def redact_value(value: Any) -> Any:
    if not isinstance(value, str):
        return value
    if re.fullmatch(r"\d{10,}", value):
        return f"{value[:2]}***{value[-2:]}"
    if "X-Amz-Signature=" in value:
        return "[redacted-url]"
    if re.search(r"(secret|token|password)[=:]", value, re.IGNORECASE):
        return "[redacted]"
    return value


def _redact_field(key: str, value: Any) -> Any:
    if any(part in key.lower() for part in ("secret", "token", "password")):
        return "***"
    return redact_value(value)


def bind_context(**fields: Any) -> None:
    safe = {key: _redact_field(key, value) for key, value in fields.items()}
    current = dict(_context.get())
    current.update(safe)
    _context.set(current)


def structured_record(message: str, **fields: Any) -> dict[str, Any]:
    record = dict(_context.get())
    record.update({key: _redact_field(key, value) for key, value in fields.items()})
    record["message"] = message
    return record
