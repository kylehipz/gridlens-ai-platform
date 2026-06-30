import re
from typing import Any

SENSITIVE_FIELD_PARTS = (
    "apikey",
    "authorization",
    "credential",
    "password",
    "secret",
    "signature",
    "signedurl",
    "source",
    "prompt",
    "record",
    "token",
)

SENSITIVE_IDENTIFIER_FIELD_PARTS = (
    "accountid",
    "accountnumber",
    "meternumber",
    "meterid",
    "participantid",
    "participantnumber",
    "utilityaccountid",
    "utilityaccountnumber",
)

SAFE_TELEMETRY_FIELD_NAMES = {
    "error_module_path",
    "error_file_path",
    "error_function",
    "error_line_no",
    "source_module",
    "source_function",
    "source_line_no",
}

SIGNED_URL_PATTERN = re.compile(r"([?&](X-Amz-Signature|Signature)=)[^&]+", re.IGNORECASE)
BEARER_PATTERN = re.compile(r"Bearer\s+[A-Za-z0-9._~+/=-]+", re.IGNORECASE)
SECRET_ASSIGNMENT_PATTERN = re.compile(
    r"\b(secret|token|password|api[_-]?key|credential)=\S+", re.IGNORECASE
)
ACCOUNT_NUMBER_PATTERN = re.compile(r"\b\d{10,}\b")


def redact_value(value: Any) -> Any:
    if isinstance(value, dict):
        return redact_fields(value)
    if isinstance(value, list):
        return [redact_value(item) for item in value]
    if isinstance(value, tuple):
        return tuple(redact_value(item) for item in value)
    if not isinstance(value, str):
        return value

    if "X-Amz-Signature=" in value:
        return "[redacted-url]"
    if BEARER_PATTERN.search(value):
        return "[redacted]"
    if SECRET_ASSIGNMENT_PATTERN.search(value):
        return "[redacted]"
    if ACCOUNT_NUMBER_PATTERN.fullmatch(value):
        return _mask_account_number(value)

    redacted = SIGNED_URL_PATTERN.sub(r"\1[redacted]", value)
    return ACCOUNT_NUMBER_PATTERN.sub(lambda match: _mask_account_number(match.group(0)), redacted)


def redact_fields(fields: dict[str, Any]) -> dict[str, Any]:
    return {key: redact_field(key, value) for key, value in fields.items()}


def redact_field(key: str, value: Any) -> Any:
    if key in SAFE_TELEMETRY_FIELD_NAMES:
        return redact_value(value)
    normalized = "".join(character for character in key.lower() if character.isalnum())
    if any(part in normalized for part in SENSITIVE_FIELD_PARTS):
        return _safe_sensitive_value(value)
    if any(part in normalized for part in SENSITIVE_IDENTIFIER_FIELD_PARTS):
        return _safe_sensitive_value(value)
    return redact_value(value)


def safe_attributes(fields: dict[str, Any]) -> dict[str, str | int | float | bool]:
    safe: dict[str, str | int | float | bool] = {}
    for key, value in redact_fields(fields).items():
        if value is None:
            continue
        if isinstance(value, str | int | float | bool):
            safe[key] = value
        else:
            safe[key] = str(value)
    return safe


def _mask_account_number(value: str) -> str:
    return f"{'*' * max(len(value) - 4, 0)}{value[-4:]}"


def _safe_sensitive_value(value: Any) -> str:
    if value is None:
        return "***"
    if isinstance(value, str) and ACCOUNT_NUMBER_PATTERN.fullmatch(value):
        return _mask_account_number(value)
    return "***"
