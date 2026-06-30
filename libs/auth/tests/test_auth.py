import unittest

from gridlens_auth import (
    AuthenticationError,
    AuthMode,
    AuthSettings,
    JwksTokenValidator,
    PermissionDenied,
    TestTokenValidator,
    bearer_token,
    require_role,
)
from gridlens_contracts.roles import PlatformRole, Role
from gridlens_contracts.tenant_context import ActorContext, TenantContext


class FakeJwksVerifier:
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
    def test_test_token_attaches_principal_tenant_context_and_role_in_test_mode(self):
        principal = TestTokenValidator(settings=AuthSettings.test()).validate(
            "dev:user_a:tenant_a:Analyst", request_id="req_1", correlation_id="corr_1"
        )
        self.assertEqual("user_a", principal.subject)
        self.assertEqual("user_a@example.test", principal.email)
        self.assertIsNotNone(principal.tenant_context)
        assert principal.tenant_context is not None
        self.assertEqual("tenant_a", principal.tenant_context.tenant_id)
        self.assertEqual("user_a", principal.tenant_context.actor.actor_id)
        self.assertIn(Role.ANALYST, principal.tenant_context.roles)
        self.assertEqual("req_1", principal.tenant_context.request_id)
        self.assertEqual("corr_1", principal.tenant_context.correlation_id)
        require_role(principal.tenant_context, {Role.ANALYST})

    def test_test_token_is_rejected_outside_test_mode(self):
        settings = AuthSettings(mode=AuthMode.COGNITO, issuer="issuer", audience="aud", jwks_url="jwks")
        with self.assertRaises(AuthenticationError):
            TestTokenValidator(settings=settings).validate(
                "dev:user_a:tenant_a:Analyst", request_id="req", correlation_id="corr"
            )

    def test_test_token_rejects_malformed_or_unknown_role(self):
        validator = TestTokenValidator(settings=AuthSettings.test())
        for token in ("", "Bearer jwt", "dev::tenant_a:Analyst", "dev:user_a:tenant_a:Owner"):
            with self.subTest(token=token):
                with self.assertRaises(AuthenticationError):
                    validator.validate(token, request_id="req", correlation_id="corr")

    def test_bearer_token_maps_missing_or_invalid_credentials_to_auth_failure(self):
        self.assertEqual("jwt", bearer_token("Bearer jwt"))
        for header in (None, "", "Basic abc", "Bearer "):
            with self.subTest(header=header):
                with self.assertRaises(AuthenticationError):
                    bearer_token(header)

    def test_auth_settings_from_env_builds_cognito_settings(self):
        settings = AuthSettings.from_env(
            {
                "AUTH_MODE": "cognito",
                "COGNITO_ISSUER": "https://issuer.example.test",
                "COGNITO_CLIENT_ID": "gridlens-client",
                "COGNITO_JWKS_URL": "https://issuer.example.test/jwks.json",
            }
        )
        self.assertEqual(AuthMode.COGNITO, settings.mode)
        self.assertEqual("https://issuer.example.test", settings.issuer)
        self.assertEqual("gridlens-client", settings.audience)
        self.assertEqual("https://issuer.example.test/jwks.json", settings.jwks_url)

    def test_auth_settings_from_env_rejects_test_mode_outside_test_runtime(self):
        with self.assertRaises(AuthenticationError):
            AuthSettings.from_env({"AUTH_MODE": "test", "GRIDLENS_RUNTIME_MODE": "local"})
        self.assertEqual(
            AuthMode.TEST,
            AuthSettings.from_env({"AUTH_MODE": "test", "GRIDLENS_RUNTIME_MODE": "test"}).mode,
        )

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
        verifier = FakeJwksVerifier()
        settings = AuthSettings.cognito(
            issuer="https://issuer.example.test",
            audience="gridlens",
            jwks_url="https://issuer.example.test/.well-known/jwks.json",
        )
        principal = JwksTokenValidator.from_settings(settings, verifier=verifier).validate(
            "jwt", request_id="req", correlation_id="corr"
        )
        self.assertEqual([("jwt", "https://issuer.example.test", "gridlens")], verifier.calls)
        self.assertIsNotNone(principal.tenant_context)
        assert principal.tenant_context is not None
        self.assertEqual("user_jwks", principal.subject)
        self.assertEqual("tenant_a", principal.tenant_context.tenant_id)
        self.assertIn(Role.TENANT_ADMIN, principal.tenant_context.roles)
        self.assertEqual("req", principal.tenant_context.request_id)
        self.assertEqual("corr", principal.tenant_context.correlation_id)
        self.assertIn(PlatformRole.PLATFORM_OPERATOR, principal.tenant_context.actor.platform_roles)

    def test_jwks_validator_rejects_bad_claim_shape(self):
        class BadVerifier:
            def verify(self, token, *, issuer, audience):
                return {"tenant_roles": ["Owner"]}

        with self.assertRaises(AuthenticationError):
            JwksTokenValidator(
                issuer="https://issuer.example.test", audience="gridlens", verifier=BadVerifier()
            ).validate("jwt", request_id="req", correlation_id="corr")


if __name__ == "__main__":
    unittest.main()
