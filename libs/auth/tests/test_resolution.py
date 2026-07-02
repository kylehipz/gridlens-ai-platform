import unittest
from dataclasses import replace

from gridlens_auth import (
    AppUserRecord,
    IdentityResolutionError,
    PlatformRoleAssignmentRecord,
    Principal,
    PrincipalResolver,
    TenantMembershipRecord,
)
from gridlens_contracts.roles import PlatformRole, Role
from gridlens_contracts.tenant_context import ActorContext, TenantContext


class FakeIdentityRepository:
    def __init__(
        self,
        *,
        user: AppUserRecord | None,
        membership: TenantMembershipRecord | None,
        platform_roles: list[PlatformRoleAssignmentRecord] | None = None,
    ):
        self.user = user
        self.membership = membership
        self.platform_roles = platform_roles or []
        self.user_calls = []
        self.membership_calls = []
        self.platform_role_calls = []

    def get_user_by_external_identity(self, provider: str, subject: str):
        self.user_calls.append((provider, subject))
        return self.user

    def list_active_platform_roles_for_user(self, user_id: str):
        self.platform_role_calls.append(user_id)
        return [assignment for assignment in self.platform_roles if assignment.user_id == user_id]

    def get_membership_for_user_tenant(self, *, user_id: str, tenant_id: str):
        self.membership_calls.append((user_id, tenant_id))
        if self.membership and self.membership.user_id == user_id and self.membership.tenant_id == tenant_id:
            return self.membership
        return None


USER = AppUserRecord(
    id="user_1",
    email="jordan.lee@kylehipz.dev",
    display_name="Jordan Lee",
    external_auth_provider="cognito",
    external_subject="cognito-sub-1",
    status="active",
)
MEMBERSHIP = TenantMembershipRecord(
    id="membership_1",
    tenant_id="tenant_northwind",
    user_id="user_1",
    role="Analyst",
    status="active",
)
PLATFORM_ROLE = PlatformRoleAssignmentRecord(
    id="platform_role_1",
    user_id="user_1",
    role="Platform Admin",
    status="active",
)


def _jwt_principal() -> Principal:
    return Principal(
        subject="cognito-sub-1",
        email="claim@example.com",
        tenant_context=TenantContext(
            tenant_id="client_claim_tenant",
            actor=ActorContext(
                actor_type="user",
                actor_id="cognito-sub-1",
                platform_roles=(),
            ),
            roles=(Role.VIEWER,),
            membership_status="active",
            request_id="claim_req",
            correlation_id="claim_corr",
        ),
    )


class PrincipalResolutionTests(unittest.TestCase):
    def test_resolves_cognito_subject_to_active_user_and_membership(self):
        repo = FakeIdentityRepository(user=USER, membership=MEMBERSHIP, platform_roles=[PLATFORM_ROLE])

        principal = PrincipalResolver(repo).resolve(
            _jwt_principal(),
            tenant_id="tenant_northwind",
            request_id="req_1",
            correlation_id="corr_1",
        )

        self.assertEqual([("cognito", "cognito-sub-1")], repo.user_calls)
        self.assertEqual(["user_1"], repo.platform_role_calls)
        self.assertEqual([("user_1", "tenant_northwind")], repo.membership_calls)
        self.assertEqual("cognito-sub-1", principal.subject)
        self.assertEqual("user_1", principal.user_id)
        self.assertEqual("jordan.lee@kylehipz.dev", principal.email)
        self.assertIsNotNone(principal.tenant_context)
        assert principal.tenant_context is not None
        self.assertEqual("tenant_northwind", principal.tenant_context.tenant_id)
        self.assertEqual("user_1", principal.tenant_context.actor.actor_id)
        self.assertEqual("Jordan Lee", principal.tenant_context.actor.display_name)
        self.assertEqual((PlatformRole.PLATFORM_ADMIN,), principal.tenant_context.actor.platform_roles)
        self.assertEqual((Role.ANALYST,), principal.tenant_context.roles)
        self.assertEqual("membership_1", principal.tenant_context.membership_id)
        self.assertEqual("active", principal.tenant_context.membership_status)
        self.assertEqual("req_1", principal.tenant_context.request_id)
        self.assertEqual("corr_1", principal.tenant_context.correlation_id)

    def test_resolves_platform_actor_without_tenant_membership(self):
        repo = FakeIdentityRepository(user=USER, membership=None, platform_roles=[PLATFORM_ROLE])

        principal = PrincipalResolver(repo).resolve(
            _jwt_principal(),
            tenant_id=None,
            request_id="req_1",
            correlation_id="corr_1",
        )

        self.assertEqual([("cognito", "cognito-sub-1")], repo.user_calls)
        self.assertEqual(["user_1"], repo.platform_role_calls)
        self.assertEqual([], repo.membership_calls)
        self.assertIsNone(principal.tenant_context)
        self.assertIsNotNone(principal.actor)
        assert principal.actor is not None
        self.assertEqual("user_1", principal.actor.actor_id)
        self.assertEqual((PlatformRole.PLATFORM_ADMIN,), principal.actor.platform_roles)

    def test_denies_unknown_or_disabled_user(self):
        for user in (None, replace(USER, status="disabled")):
            with self.subTest(user=user):
                with self.assertRaises(IdentityResolutionError):
                    PrincipalResolver(FakeIdentityRepository(user=user, membership=MEMBERSHIP)).resolve(
                        _jwt_principal(),
                        tenant_id="tenant_northwind",
                        request_id="req",
                        correlation_id="corr",
                    )

    def test_denies_missing_inactive_wrong_tenant_or_invalid_membership_role(self):
        denied_memberships = (
            None,
            replace(MEMBERSHIP, status="disabled"),
            replace(MEMBERSHIP, tenant_id="tenant_cascade"),
            replace(MEMBERSHIP, role="Owner"),
        )
        for membership in denied_memberships:
            with self.subTest(membership=membership):
                with self.assertRaises(IdentityResolutionError):
                    PrincipalResolver(FakeIdentityRepository(user=USER, membership=membership)).resolve(
                        _jwt_principal(),
                        tenant_id="tenant_northwind",
                        request_id="req",
                        correlation_id="corr",
                    )


if __name__ == "__main__":
    unittest.main()
