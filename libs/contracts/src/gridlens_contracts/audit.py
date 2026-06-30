from dataclasses import dataclass, field
from datetime import UTC, datetime
from enum import StrEnum
from typing import Any


class AuditAction(StrEnum):
    TENANT_CREATED = "tenant.created"
    TENANT_UPDATED = "tenant.updated"
    AUTHORIZATION_DENIED = "authorization.denied"
    MEMBER_INVITED = "member.invited"
    MEMBER_DEACTIVATED = "member.deactivated"
    FILE_UPLOADED = "file.uploaded"
    JOB_RETRIED = "job.retried"


def is_dotted_action(value: str) -> bool:
    left, sep, right = value.partition(".")
    return bool(left and sep and right and value == value.lower())


@dataclass(frozen=True)
class AuditContext:
    request_id: str | None = None
    correlation_id: str | None = None
    trace_id: str | None = None
    span_id: str | None = None

    def to_dict(self) -> dict[str, str]:
        return {
            key: value
            for key, value in {
                "request_id": self.request_id,
                "correlation_id": self.correlation_id,
                "trace_id": self.trace_id,
                "span_id": self.span_id,
            }.items()
            if value is not None
        }


@dataclass(frozen=True)
class AuditEvent:
    action: str
    tenant_id: str
    actor_id: str
    target_type: str
    target_id: str
    context: AuditContext = field(default_factory=AuditContext)
    metadata: dict[str, Any] = field(default_factory=dict)
    occurred_at: datetime = field(default_factory=lambda: datetime.now(UTC))

    def to_dict(self) -> dict[str, Any]:
        return {
            "action": self.action,
            "tenant_id": self.tenant_id,
            "actor_id": self.actor_id,
            "target_type": self.target_type,
            "target_id": self.target_id,
            "context": self.context.to_dict(),
            "metadata": self.metadata,
            "occurred_at": self.occurred_at.isoformat(),
        }
