from dataclasses import dataclass, field
from datetime import UTC, datetime
from typing import Any

from .tenant_context import ActorContext


@dataclass(frozen=True)
class RetryMetadata:
    attempt_number: int = 1
    max_attempts: int = 3

    def next_attempt(self) -> "RetryMetadata":
        return RetryMetadata(
            attempt_number=self.attempt_number + 1,
            max_attempts=self.max_attempts,
        )


@dataclass(frozen=True)
class EventEnvelope:
    event_type: str
    event_version: int
    tenant_id: str
    correlation_id: str
    idempotency_key: str
    actor: ActorContext
    source_resource_ids: dict[str, str]
    payload: dict[str, Any]
    retry: RetryMetadata = field(default_factory=RetryMetadata)
    occurred_at: datetime = field(default_factory=lambda: datetime.now(UTC))

    def to_dict(self) -> dict[str, Any]:
        return {
            "event_type": self.event_type,
            "event_version": self.event_version,
            "tenant_id": self.tenant_id,
            "correlation_id": self.correlation_id,
            "idempotency_key": self.idempotency_key,
            "actor": {
                "actor_type": self.actor.actor_type,
                "actor_id": self.actor.actor_id,
                "display_name": self.actor.display_name,
            },
            "source_resource_ids": self.source_resource_ids,
            "payload": self.payload,
            "retry": {
                "attempt_number": self.retry.attempt_number,
                "max_attempts": self.retry.max_attempts,
            },
            "occurred_at": self.occurred_at.isoformat(),
        }
