from dataclasses import dataclass
from typing import Any


SENSITIVE_DETAIL_KEYS = {
    "stack",
    "traceback",
    "sql",
    "prompt",
    "retrieved_context",
    "credential",
    "credentials",
    "password",
    "token",
    "signed_url",
}


def sanitize_details(value: Any) -> Any:
    if isinstance(value, dict):
        return {
            key: sanitize_details(nested)
            for key, nested in value.items()
            if key.lower() not in SENSITIVE_DETAIL_KEYS
        }
    if isinstance(value, list):
        return [sanitize_details(item) for item in value]
    return value


@dataclass(frozen=True)
class ErrorEnvelope:
    code: str
    message: str
    request_id: str
    details: dict[str, Any] | None = None

    def to_dict(self) -> dict[str, Any]:
        payload: dict[str, Any] = {
            "code": self.code,
            "message": self.message,
            "request_id": self.request_id,
        }
        if self.details:
            payload["details"] = sanitize_details(self.details)
        return payload
