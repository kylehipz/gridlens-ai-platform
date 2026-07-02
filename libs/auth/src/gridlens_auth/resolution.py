from dataclasses import dataclass
from typing import Protocol

from gridlens_contracts.roles import PlatformRole, Role
from gridlens_contracts.tenant_context import ActorContext, TenantContext

from .tokens import AuthenticationError, Principal


class IdentityResolutionError(AuthenticationError):
    """Safe failure while mapping an authenticated subject to GridLens identity state."""


@dataclass(frozen=True)
class AppUserRecord:
    id: str
    email: str
    display_name: str
    external_auth_provider: str
    external_subject: str
    status: str


@dataclass(frozen=True)
class TenantMembershipRecord:
    id: str
    tenant_id: str
    user_id: str
    role: str
    status: str


@dataclass(frozen=True)
class PlatformRoleAssignmentRecord:
    id: str
    user_id: str
    role: str
    status: str


class IdentityRepository(Protocol):
    def get_user_by_external_identity(self, provider: str, subject: str) -> AppUserRecord | None:
        ...

    def list_active_platform_roles_for_user(self, user_id: str) -> list[PlatformRoleAssignmentRecord]:
        ...

    def get_membership_for_user_tenant(
        self, *, user_id: str, tenant_id: str
    ) -> TenantMembershipRecord | None:
        ...


class PrincipalResolver:
    def __init__(self, repository: IdentityRepository, *, external_auth_provider: str = "cognito"):
        self._repository = repository
        self._external_auth_provider = external_auth_provider

    def resolve(
        self,
        principal: Principal,
        *,
        tenant_id: str | None,
        request_id: str,
        correlation_id: str,
    ) -> Principal:
        user = self._repository.get_user_by_external_identity(
            self._external_auth_provider, principal.subject
        )
        if user is None or user.status != "active":
            raise IdentityResolutionError("Authenticated user is not available.")

        try:
            platform_roles = tuple(
                PlatformRole(assignment.role)
                for assignment in self._repository.list_active_platform_roles_for_user(str(user.id))
            )
        except ValueError as error:
            raise IdentityResolutionError("Authenticated user is not available.") from error

        actor = ActorContext(
            actor_type="user",
            actor_id=str(user.id),
            display_name=user.display_name,
            platform_roles=platform_roles,
        )

        if tenant_id is None:
            return Principal(
                subject=principal.subject,
                email=user.email,
                user_id=str(user.id),
                external_auth_provider=user.external_auth_provider,
                tenant_context=None,
                actor_context=actor,
            )

        membership = self._repository.get_membership_for_user_tenant(
            user_id=str(user.id), tenant_id=tenant_id
        )
        if membership is None or membership.status != "active":
            raise IdentityResolutionError("Tenant membership is not available.")

        try:
            role = Role(membership.role)
        except ValueError as error:
            raise IdentityResolutionError("Tenant membership is not available.") from error

        return Principal(
            subject=principal.subject,
            email=user.email,
            user_id=str(user.id),
            external_auth_provider=user.external_auth_provider,
            tenant_context=TenantContext(
                tenant_id=str(membership.tenant_id),
                actor=actor,
                roles=(role,),
                membership_id=str(membership.id),
                membership_status=membership.status,
                request_id=request_id,
                correlation_id=correlation_id,
            ),
        )
