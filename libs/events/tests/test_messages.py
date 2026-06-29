import json
import unittest

from gridlens_contracts.tenant_context import ActorContext
from gridlens_events import build_event, event_source_id, idempotency_key, to_queue_message


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
        body = json.loads(message["MessageBody"])
        for field in ("tenant_id", "correlation_id", "actor", "retry", "idempotency_key"):
            self.assertIn(field, body)

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
