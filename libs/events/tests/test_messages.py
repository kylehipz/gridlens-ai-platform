import json
import unittest
from typing import cast

from gridlens_contracts.tenant_context import ActorContext
from gridlens_events import (
    build_event,
    event_source_id,
    idempotency_key,
    queue_message_attributes,
    to_queue_message,
)


class EventTests(unittest.TestCase):
    def test_event_envelope_and_queue_message_include_worker_fields(self):
        actor = ActorContext.system("worker")
        event = build_event(
            event_type="generic.workflow.requested",
            tenant_id="tenant_a",
            correlation_id="corr_1",
            actor=actor,
            source_resource_ids={"dataset_id": "dataset_1"},
            payload={"ok": True},
        )
        self.assertEqual("tenant_a:generic.workflow.requested:dataset_1", event.idempotency_key)
        message = to_queue_message(event)
        body = json.loads(cast(str, message["MessageBody"]))
        for field in ("tenant_id", "correlation_id", "actor", "retry", "idempotency_key"):
            self.assertIn(field, body)

    def test_queue_message_includes_request_and_trace_context(self):
        event = build_event(
            event_type="generic.workflow.requested",
            tenant_id="tenant_a",
            correlation_id="corr_1",
            request_id="req_1",
            trace_id="trace_1",
            span_id="span_1",
            actor=ActorContext.system("worker"),
            source_resource_ids={"job_id": "job_1"},
            payload={},
        )

        message = to_queue_message(event)
        attributes = cast(dict[str, dict[str, str]], message["MessageAttributes"])
        self.assertEqual("req_1", attributes["request_id"]["StringValue"])
        self.assertEqual("trace_1", attributes["trace_id"]["StringValue"])
        self.assertEqual("span_1", attributes["span_id"]["StringValue"])
        self.assertEqual(
            {
                "tenant_id": "tenant_a",
                "correlation_id": "corr_1",
                "idempotency_key": event.idempotency_key,
                "request_id": "req_1",
                "trace_id": "trace_1",
                "span_id": "span_1",
            },
            queue_message_attributes(event),
        )

    def test_retry_attempt_preserves_idempotency_key_and_increments_attempt(self):
        first = build_event(
            event_type="generic.workflow.requested",
            tenant_id="tenant_a",
            correlation_id="corr_1",
            actor=ActorContext.system("worker"),
            source_resource_ids={"dataset_id": "dataset_1"},
            payload={},
        )
        retry = build_event(
            event_type=first.event_type,
            tenant_id=first.tenant_id,
            correlation_id=first.correlation_id,
            actor=first.actor,
            source_resource_ids=first.source_resource_ids,
            payload=first.payload,
            attempt_number=2,
        )
        self.assertEqual(first.idempotency_key, retry.idempotency_key)
        self.assertEqual(2, retry.retry.attempt_number)
        self.assertEqual(first.idempotency_key, idempotency_key(tenant_id="tenant_a", event_type=first.event_type, source_id="dataset_1"))

    def test_multi_resource_event_idempotency_key_is_order_stable(self):
        actor = ActorContext.system("worker")
        first = build_event(
            event_type="generic.workflow.requested",
            tenant_id="tenant_a",
            correlation_id="corr_1",
            actor=actor,
            source_resource_ids={"dataset_id": "dataset_1", "job_id": "job_1"},
            payload={},
        )
        second = build_event(
            event_type="generic.workflow.requested",
            tenant_id="tenant_a",
            correlation_id="corr_1",
            actor=actor,
            source_resource_ids={"job_id": "job_1", "dataset_id": "dataset_1"},
            payload={},
        )
        self.assertEqual(first.idempotency_key, second.idempotency_key)
        self.assertEqual(
            "dataset_id=dataset_1|job_id=job_1",
            event_source_id({"job_id": "job_1", "dataset_id": "dataset_1"}),
        )

    def test_event_requires_source_resource_ids(self):
        with self.assertRaisesRegex(ValueError, "source_resource_ids"):
            build_event(
                event_type="generic.workflow.requested",
                tenant_id="tenant_a",
                correlation_id="corr_1",
                actor=ActorContext.system("worker"),
                source_resource_ids={},
                payload={},
            )
        with self.assertRaisesRegex(ValueError, "non-empty"):
            build_event(
                event_type="generic.workflow.requested",
                tenant_id="tenant_a",
                correlation_id="corr_1",
                actor=ActorContext.system("worker"),
                source_resource_ids={"dataset_id": "dataset_1", "job_id": ""},
                payload={},
            )


if __name__ == "__main__":
    unittest.main()
