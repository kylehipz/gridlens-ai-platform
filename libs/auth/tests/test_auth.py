import unittest

from gridlens_auth import DevTokenValidator, JwksTokenValidator, PermissionDenied, require_role
from gridlens_contracts.roles import PlatformRole, Role
from gridlens_contracts.tenant_context import ActorContext, TenantContext


class FakeKeyProvider:
    def __init__(self):
        self.calls = []

    def verify(self, token, *, issuer, audience):
        self.calls.append((token, issuer, audience))
        return {
            "sub": "user_jwks",
            "email": "user@example.test",
            "tenant_id": "tenant_a",
            "tenant_roles": ["Tenant Admin"],
            "membership_id": "member_1",
            "membership_status": "active",
            "platform_roles": ["Platform Operator"],
        }


class AuthTests(unittest.TestCase):
    def test_dev_token_attaches_principal_tenant_context_and_role(self):
        principal = DevTokenValidator().validate(
            "dev:user_a:tenant_a:Analyst", request_id="req_1", correlation_id="corr_1"
        )
        self.assertEqual("user_a", principal.subject)
        self.assertIn(Role.ANALYST, principal.tenant_context.roles)
        require_role(principal.tenant_context, {Role.ANALYST})

    def test_permission_denies_missing_inactive_and_wrong_role(self):
        with self.assertRaises(PermissionDenied):
            require_role(None, {Role.ANALYST})
        inactive = TenantContext(
            tenant_id="tenant_a",
            actor=ActorContext(actor_type="user", actor_id="user_a"),
            roles=(Role.ANALYST,),
            membership_status="disabled",
            request_id="req",
            correlation_id="corr",
        )
        with self.assertRaises(PermissionDenied):
            require_role(inactive, {Role.ANALYST})
        active_viewer = TenantContext(
            tenant_id="tenant_a",
            actor=ActorContext(actor_type="user", actor_id="user_a"),
            roles=(Role.VIEWER,),
            membership_status="active",
            request_id="req",
            correlation_id="corr",
        )
        with self.assertRaises(PermissionDenied):
            require_role(active_viewer, {Role.ANALYST, Role.TENANT_ADMIN})

    def test_jwks_ready_validator_uses_injected_provider_without_network(self):
        provider = FakeKeyProvider()
        principal = JwksTokenValidator(
            issuer="https://issuer.example.test", audience="gridlens", key_provider=provider
        ).validate("jwt", request_id="req", correlation_id="corr")
        self.assertEqual([("jwt", "https://issuer.example.test", "gridlens")], provider.calls)
        self.assertIn(PlatformRole.PLATFORM_OPERATOR, principal.tenant_context.actor.platform_roles)


if __name__ == "__main__":
    unittest.main()
