import re
from contextvars import ContextVar
from typing import Any

_context: ContextVar[dict[str, Any] | None] = ContextVar("gridlens_log_context", default=None)


def redact_value(value: Any) -> Any:
    if not isinstance(value, str):
        return value
    if re.fullmatch(r"\d{10,}", value):
        return f"{value[:2]}***{value[-2:]}"
    if "X-Amz-Signature=" in value:
        return "[redacted-url]"
    if re.search(r"Bearer\s+\S+", value, re.IGNORECASE):
        return "[redacted]"
    if re.search(r"(secret|token|password|api[_-]?key|credential)[=:]", value, re.IGNORECASE):
        return "[redacted]"
    return value


def _redact_field(key: str, value: Any) -> Any:
    normalized = "".join(character for character in key.lower() if character.isalnum())
    sensitive_parts = ("apikey", "authorization", "credential", "password", "secret", "signature", "token")
    if any(part in normalized for part in sensitive_parts):
        return "***"
    return redact_value(value)


def _current_context() -> dict[str, Any]:
    return dict(_context.get() or {})


def bind_context(**fields: Any) -> None:
    safe = {key: _redact_field(key, value) for key, value in fields.items()}
    current = _current_context()
    current.update(safe)
    _context.set(current)


def structured_record(message: str, **fields: Any) -> dict[str, Any]:
    record = _current_context()
    record.update({key: _redact_field(key, value) for key, value in fields.items()})
    record["message"] = message
    return record
