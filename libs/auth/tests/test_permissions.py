import unittest

from gridlens_auth import (
    AuthorizationDeniedAuditRecord,
    PermissionDenied,
    has_platform_role,
    require_platform_role,
    require_tenant_role,
)
from gridlens_contracts.roles import PlatformRole, Role
from gridlens_contracts.tenant_context import ActorContext, TenantContext


class FakeAuditSink:
    def __init__(self):
        self.records: list[AuthorizationDeniedAuditRecord] = []

    def record_denied(self, record: AuthorizationDeniedAuditRecord) -> None:
        self.records.append(record)


def _tenant_context(
    *,
    tenant_id: str = "tenant_northwind",
    roles: tuple[Role, ...] = (Role.ANALYST,),
    membership_status: str = "active",
) -> TenantContext:
    return TenantContext(
        tenant_id=tenant_id,
        actor=ActorContext(
            actor_type="user",
            actor_id="user_1",
            platform_roles=(PlatformRole.PLATFORM_OPERATOR,),
        ),
        roles=roles,
        membership_id="membership_1",
        membership_status=membership_status,
        request_id="req_1",
        correlation_id="corr_1",
    )


class PermissionHelperTests(unittest.TestCase):
    def test_tenant_role_allows_matching_active_membership(self):
        require_tenant_role(
            _tenant_context(),
            tenant_id="tenant_northwind",
            allowed={Role.ANALYST, Role.TENANT_ADMIN},
            action="files.upload_url.create",
        )

    def test_tenant_role_denies_missing_context(self):
        sink = FakeAuditSink()
        with self.assertRaises(PermissionDenied) as error:
            require_tenant_role(
                None,
                tenant_id="tenant_northwind",
                allowed={Role.ANALYST},
                action="files.upload_url.create",
                audit_sink=sink,
            )
        self.assertEqual("missing_tenant_context", error.exception.reason_code)
        self.assertEqual("denied", sink.records[0].outcome)
        self.assertEqual("tenant_northwind", sink.records[0].tenant_id)
        self.assertIsNone(sink.records[0].actor_id)
        self.assertEqual({"reason": "missing_tenant_context"}, sink.records[0].metadata)

    def test_tenant_role_denies_inactive_wrong_tenant_and_insufficient_role(self):
        cases = (
            ("inactive_membership", _tenant_context(membership_status="disabled"), "tenant_northwind"),
            ("wrong_tenant", _tenant_context(), "tenant_cascade"),
            ("insufficient_tenant_role", _tenant_context(roles=(Role.VIEWER,)), "tenant_northwind"),
        )
        for reason, context, tenant_id in cases:
            sink = FakeAuditSink()
            with self.subTest(reason=reason):
                with self.assertRaises(PermissionDenied) as error:
                    require_tenant_role(
                        context,
                        tenant_id=tenant_id,
                        allowed={Role.ANALYST, Role.TENANT_ADMIN},
                        action="files.upload_url.create",
                        audit_sink=sink,
                    )
                self.assertEqual(reason, error.exception.reason_code)
                self.assertEqual(1, len(sink.records))
                self.assertEqual("user_1", sink.records[0].actor_id)
                self.assertEqual(tenant_id, sink.records[0].tenant_id)
                self.assertEqual("files.upload_url.create", sink.records[0].action)
                self.assertEqual("denied", sink.records[0].outcome)
                self.assertEqual("req_1", sink.records[0].request_id)
                self.assertEqual({"reason": reason}, sink.records[0].metadata)

    def test_platform_role_check_allows_and_denies(self):
        actor = _tenant_context().actor
        self.assertTrue(has_platform_role(actor.platform_roles, PlatformRole.PLATFORM_OPERATOR))
        require_platform_role(
            actor,
            required=PlatformRole.PLATFORM_OPERATOR,
            action="platform.settings.update",
            request_id="req_1",
        )

        sink = FakeAuditSink()
        with self.assertRaises(PermissionDenied) as error:
            require_platform_role(
                actor,
                required=PlatformRole.PLATFORM_ADMIN,
                action="platform.settings.update",
                request_id="req_1",
                tenant_id="tenant_northwind",
                audit_sink=sink,
            )

        self.assertEqual("insufficient_platform_role", error.exception.reason_code)
        self.assertEqual("user_1", sink.records[0].actor_id)
        self.assertEqual("tenant_northwind", sink.records[0].tenant_id)
        self.assertEqual({"reason": "insufficient_platform_role"}, sink.records[0].metadata)


if __name__ == "__main__":
    unittest.main()
