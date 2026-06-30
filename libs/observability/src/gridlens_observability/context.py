from contextvars import ContextVar, Token
from dataclasses import dataclass
from typing import Any

from .redaction import redact_fields

_context: ContextVar[dict[str, Any] | None] = ContextVar(
    "gridlens_observability_context", default=None
)


@dataclass(frozen=True)
class ObservabilityContext:
    request_id: str | None = None
    correlation_id: str | None = None
    trace_id: str | None = None
    span_id: str | None = None
    tenant_id: str | None = None
    actor_id: str | None = None
    service: str | None = None
    job_id: str | None = None

    @classmethod
    def from_mapping(cls, fields: dict[str, Any]) -> "ObservabilityContext":
        return cls(
            request_id=_optional_string(fields.get("request_id")),
            correlation_id=_optional_string(fields.get("correlation_id")),
            trace_id=_optional_string(fields.get("trace_id")),
            span_id=_optional_string(fields.get("span_id")),
            tenant_id=_optional_string(fields.get("tenant_id")),
            actor_id=_optional_string(fields.get("actor_id")),
            service=_optional_string(fields.get("service")),
            job_id=_optional_string(fields.get("job_id")),
        )

    def to_dict(self) -> dict[str, str]:
        return {
            key: value
            for key, value in {
                "request_id": self.request_id,
                "correlation_id": self.correlation_id,
                "trace_id": self.trace_id,
                "span_id": self.span_id,
                "tenant_id": self.tenant_id,
                "actor_id": self.actor_id,
                "service": self.service,
                "job_id": self.job_id,
            }.items()
            if value is not None
        }


def bind_context(**fields: Any) -> Token[dict[str, Any] | None]:
    current = current_context_fields()
    current.update(redact_fields(fields))
    return _context.set(current)


def clear_context() -> None:
    _context.set(None)


def reset_context(token: Token[dict[str, Any] | None]) -> None:
    _context.reset(token)


def current_context_fields() -> dict[str, Any]:
    return dict(_context.get() or {})


def current_context() -> ObservabilityContext:
    return ObservabilityContext.from_mapping(current_context_fields())


def _optional_string(value: Any) -> str | None:
    if value is None:
        return None
    return str(value)
