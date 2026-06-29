import json

from gridlens_contracts.events import EventEnvelope, RetryMetadata
from gridlens_contracts.tenant_context import ActorContext


def idempotency_key(*, tenant_id: str, event_type: str, source_id: str) -> str:
    return f"{tenant_id}:{event_type}:{source_id}"


def event_source_id(source_resource_ids: dict[str, str]) -> str:
    if not source_resource_ids:
        raise ValueError("source_resource_ids must include at least one resource ID.")
    if any(not value for value in source_resource_ids.values()):
        raise ValueError("source_resource_ids values must be non-empty.")
    if len(source_resource_ids) == 1:
        return next(iter(source_resource_ids.values()))
    return "|".join(f"{key}={value}" for key, value in sorted(source_resource_ids.items()))


def build_event(
    *,
    event_type: str,
    tenant_id: str,
    correlation_id: str,
    actor: ActorContext,
    source_resource_ids: dict[str, str],
    payload: dict,
    attempt_number: int = 1,
) -> EventEnvelope:
    source_id = event_source_id(source_resource_ids)
    return EventEnvelope(
        event_type=event_type,
        event_version=1,
        tenant_id=tenant_id,
        correlation_id=correlation_id,
        idempotency_key=idempotency_key(
            tenant_id=tenant_id, event_type=event_type, source_id=source_id
        ),
        actor=actor,
        source_resource_ids=source_resource_ids,
        payload=payload,
        retry=RetryMetadata(attempt_number=attempt_number),
    )


def to_queue_message(event: EventEnvelope) -> dict[str, object]:
    payload = event.to_dict()
    return {
        "MessageBody": json.dumps(payload, sort_keys=True),
        "MessageAttributes": {
            "tenant_id": {"DataType": "String", "StringValue": event.tenant_id},
            "correlation_id": {"DataType": "String", "StringValue": event.correlation_id},
            "idempotency_key": {"DataType": "String", "StringValue": event.idempotency_key},
        },
    }
