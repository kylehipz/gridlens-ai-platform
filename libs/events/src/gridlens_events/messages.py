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
    request_id: str | None = None,
    trace_id: str | None = None,
    span_id: str | None = None,
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
        request_id=request_id,
        trace_id=trace_id,
        span_id=span_id,
        retry=RetryMetadata(attempt_number=attempt_number),
    )


def to_queue_message(event: EventEnvelope) -> dict[str, object]:
    payload = event.to_dict()
    attributes = {
        "tenant_id": {"DataType": "String", "StringValue": event.tenant_id},
        "correlation_id": {"DataType": "String", "StringValue": event.correlation_id},
        "idempotency_key": {"DataType": "String", "StringValue": event.idempotency_key},
    }
    if event.request_id:
        attributes["request_id"] = {"DataType": "String", "StringValue": event.request_id}
    if event.trace_id:
        attributes["trace_id"] = {"DataType": "String", "StringValue": event.trace_id}
    if event.span_id:
        attributes["span_id"] = {"DataType": "String", "StringValue": event.span_id}
    return {
        "MessageBody": json.dumps(payload, sort_keys=True),
        "MessageAttributes": attributes,
    }


def queue_message_attributes(event: EventEnvelope) -> dict[str, str]:
    attributes = {
        "tenant_id": event.tenant_id,
        "correlation_id": event.correlation_id,
        "idempotency_key": event.idempotency_key,
    }
    if event.request_id:
        attributes["request_id"] = event.request_id
    if event.trace_id:
        attributes["trace_id"] = event.trace_id
    if event.span_id:
        attributes["span_id"] = event.span_id
    return attributes
