import json
import unittest

from gridlens_contracts.tenant_context import ActorContext
from gridlens_events import build_event, idempotency_key, to_queue_message


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


if __name__ == "__main__":
    unittest.main()
