from dataclasses import dataclass
from typing import Protocol

from gridlens_contracts.roles import PlatformRole, Role
from gridlens_contracts.tenant_context import ActorContext, TenantContext


@dataclass(frozen=True)
class Principal:
    subject: str
    email: str | None
    tenant_context: TenantContext | None


class TokenValidator(Protocol):
    def validate(self, token: str, *, request_id: str, correlation_id: str) -> Principal:
        ...


class DevTokenValidator:
    """Parse deterministic local tokens: dev:user:tenant:Role A,Role B."""

    def validate(self, token: str, *, request_id: str, correlation_id: str) -> Principal:
        parts = token.split(":", 3)
        if len(parts) != 4 or parts[0] != "dev":
            raise ValueError("Invalid local development token.")
        _, subject, tenant_id, raw_roles = parts
        roles = tuple(Role(role.strip()) for role in raw_roles.split(",") if role.strip())
        actor = ActorContext(actor_type="user", actor_id=subject, platform_roles=())
        return Principal(
            subject=subject,
            email=f"{subject}@example.test",
            tenant_context=TenantContext(
                tenant_id=tenant_id,
                actor=actor,
                roles=roles,
                membership_id=f"{tenant_id}:{subject}",
                membership_status="active",
                request_id=request_id,
                correlation_id=correlation_id,
            ),
        )


class JwksTokenValidator:
    def __init__(self, *, issuer: str, audience: str, key_provider):
        self.issuer = issuer
        self.audience = audience
        self.key_provider = key_provider

    def validate(self, token: str, *, request_id: str, correlation_id: str) -> Principal:
        claims = self.key_provider.verify(token, issuer=self.issuer, audience=self.audience)
        platform_roles = tuple(PlatformRole(value) for value in claims.get("platform_roles", ()))
        actor = ActorContext(
            actor_type="user",
            actor_id=claims["sub"],
            display_name=claims.get("name"),
            platform_roles=platform_roles,
        )
        tenant_id = claims.get("tenant_id")
        tenant_context = None
        if tenant_id:
            tenant_context = TenantContext(
                tenant_id=tenant_id,
                actor=actor,
                roles=tuple(Role(value) for value in claims.get("tenant_roles", ())),
                membership_id=claims.get("membership_id"),
                membership_status=claims.get("membership_status"),
                request_id=request_id,
                correlation_id=correlation_id,
            )
        return Principal(subject=claims["sub"], email=claims.get("email"), tenant_context=tenant_context)
