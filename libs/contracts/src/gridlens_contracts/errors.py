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

SENSITIVE_KEY_PARTS = {
    "apikey",
    "authorization",
    "credential",
    "password",
    "secret",
    "signature",
    "signedurl",
    "token",
}


def sanitize_details(value: Any) -> Any:
    if isinstance(value, dict):
        return {
            key: sanitize_details(nested)
            for key, nested in value.items()
            if not _is_sensitive_detail_key(key)
        }
    if isinstance(value, list):
        return [sanitize_details(item) for item in value]
    return value


def _is_sensitive_detail_key(key: str) -> bool:
    normalized = "".join(character for character in key.lower() if character.isalnum())
    if key.lower() in SENSITIVE_DETAIL_KEYS:
        return True
    return any(part in normalized for part in SENSITIVE_KEY_PARTS)


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
