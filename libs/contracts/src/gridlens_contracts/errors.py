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
            payload["details"] = {
                key: value
                for key, value in self.details.items()
                if key.lower() not in SENSITIVE_DETAIL_KEYS
            }
        return payload
