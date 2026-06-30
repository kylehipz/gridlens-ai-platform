import re
import unittest
from collections.abc import Mapping
from pathlib import Path
from typing import cast

from gridlens_contracts.audit import AuditAction, AuditContext, AuditEvent, is_dotted_action
from gridlens_contracts.errors import ErrorEnvelope
from gridlens_contracts.events import EventEnvelope
from gridlens_contracts.pagination import ListResponse, Pagination
from gridlens_contracts.roles import PLATFORM_ROLES, TENANT_ROLES, Role
from gridlens_contracts.statuses import STATUS_FAMILIES, EvaluationRunStatus, IngestionJobStatus
from gridlens_contracts.tenant_context import ActorContext, TenantContext

ROOT = Path(__file__).resolve().parents[3]


class ContractVocabularyTests(unittest.TestCase):
    def test_roles_match_authorization_docs(self):
        text = (ROOT / "docs/api/endpoints.md").read_text()
        documented_roles = set(re.findall(r"- `([^`]+)`: can", text))
        self.assertEqual(set(TENANT_ROLES) | set(PLATFORM_ROLES), documented_roles)
        self.assertEqual(Role.ANALYST.value, "Analyst")

    def test_status_families_match_data_model_docs(self):
        text = (ROOT / "docs/data-model.md").read_text()
        rows = re.findall(r"\| ([^|]+) \| ([^|]+) \|", text)
        documented = {
            family.strip(): tuple(re.findall(r"`([^`]+)`", values))
            for family, values in rows
            if family.strip() in STATUS_FAMILIES
        }
        expected = {
            family: tuple(member.value for member in enum_type)
            for family, enum_type in STATUS_FAMILIES.items()
        }
        self.assertEqual(expected, documented)
        self.assertIn("completed_with_warnings", {status.value for status in EvaluationRunStatus})

    def test_status_families_are_separate_even_with_overlapping_values(self):
        self.assertIsNot(EvaluationRunStatus.COMPLETED, IngestionJobStatus.COMPLETED)
        self.assertEqual(EvaluationRunStatus.COMPLETED.value, IngestionJobStatus.COMPLETED.value)


class EnvelopeTests(unittest.TestCase):
    def test_failed_response_has_stable_safe_shape(self):
        payload = ErrorEnvelope(
            code="authorization_denied",
            message="Access denied.",
            request_id="req_123",
            details={
                "resource": "dataset",
                "sql": "select * from secret",
                "nested": {
                    "prompt": "unsafe",
                    "safe": "kept",
                    "items": [{"token": "hidden", "field": "visible"}],
                },
            },
        ).to_dict()
        self.assertEqual({"code", "message", "request_id", "details"}, set(payload))
        self.assertEqual(
            {"resource": "dataset", "nested": {"safe": "kept", "items": [{"field": "visible"}]}},
            payload["details"],
        )

    def test_failed_response_strips_common_secret_key_variants(self):
        payload = ErrorEnvelope(
            code="upstream_error",
            message="Provider failed.",
            request_id="req_123",
            details={
                "access_token": "hidden",
                "api_key": "hidden",
                "authorization": "Bearer hidden",
                "nested": {
                    "refresh-token": "hidden",
                    "signedUrl": "hidden",
                    "safe": "kept",
                },
            },
        ).to_dict()
        self.assertEqual({"nested": {"safe": "kept"}}, payload["details"])

    def test_list_responses_share_pagination_fields(self):
        responses = [
            ListResponse(items=[], pagination=Pagination.from_page(limit=25, offset=0, total_count=0)).to_dict(),
            ListResponse(items=[{"audit_id": "a1"}], pagination=Pagination.from_page(limit=25, offset=0, total_count=1)).to_dict(),
            ListResponse(items=[{"evaluation_id": "e1"}], pagination=Pagination.from_page(limit=25, offset=0, total_count=50)).to_dict(),
        ]
        field_sets = {
            tuple(cast(Mapping[str, object], response["pagination"]).keys())
            for response in responses
        }
        self.assertEqual(1, len(field_sets))
        self.assertEqual(("limit", "offset", "total_count", "has_next", "next_offset"), next(iter(field_sets)))

    def test_tenant_context_and_event_envelope_include_required_fields(self):
        actor = ActorContext(actor_type="user", actor_id="user_a")
        context = TenantContext(
            tenant_id="tenant_a",
            actor=actor,
            roles=(Role.ANALYST,),
            membership_id="member_a",
            membership_status="active",
            request_id="req_1",
            correlation_id="corr_1",
        )
        self.assertTrue(context.is_active_member)
        event = EventEnvelope(
            event_type="generic.workflow.requested",
            event_version=1,
            tenant_id=context.tenant_id,
            correlation_id=context.correlation_id,
            idempotency_key="tenant_a:generic.workflow.requested:source_1",
            actor=context.actor,
            source_resource_ids={"dataset_id": "dataset_1"},
            payload={"safe": True},
        ).to_dict()
        for field in ("tenant_id", "correlation_id", "actor", "source_resource_ids", "retry", "idempotency_key", "event_type", "event_version", "occurred_at"):
            self.assertIn(field, event)
        self.assertEqual(1, event["retry"]["attempt_number"])

    def test_audit_actions_are_stable_dotted_names(self):
        self.assertIn(AuditAction.TENANT_CREATED, AuditAction)
        self.assertIn(AuditAction.AUTHORIZATION_DENIED, AuditAction)
        self.assertTrue(all(is_dotted_action(action.value) for action in AuditAction))

    def test_audit_event_can_carry_request_and_trace_context(self):
        event = AuditEvent(
            action=AuditAction.JOB_RETRIED.value,
            tenant_id="tenant_a",
            actor_id="worker",
            target_type="job",
            target_id="job_1",
            context=AuditContext(
                request_id="req_1",
                correlation_id="corr_1",
                trace_id="trace_1",
                span_id="span_1",
            ),
            metadata={"attempt": 2},
        ).to_dict()

        self.assertEqual("req_1", event["context"]["request_id"])
        self.assertEqual("corr_1", event["context"]["correlation_id"])
        self.assertEqual("trace_1", event["context"]["trace_id"])
        self.assertEqual("span_1", event["context"]["span_id"])


if __name__ == "__main__":
    unittest.main()
