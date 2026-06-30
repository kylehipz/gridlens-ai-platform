from dataclasses import dataclass, field
from typing import Any, Protocol

from gridlens_contracts.audit import AuditAction
from gridlens_contracts.errors import sanitize_details
from gridlens_contracts.roles import PlatformRole, Role
from gridlens_contracts.tenant_context import ActorContext, TenantContext


class PermissionDenied(Exception):
    def __init__(self, reason_code: str = "authorization_denied"):
        super().__init__("Access denied.")
        self.reason_code = reason_code


@dataclass(frozen=True)
class AuthorizationDeniedAuditRecord:
    action: str
    outcome: str
    request_id: str
    actor_id: str | None = None
    tenant_id: str | None = None
    metadata: dict[str, Any] = field(default_factory=dict)


class AuthorizationAuditSink(Protocol):
    def record_denied(self, record: AuthorizationDeniedAuditRecord) -> None:
        ...


def require_role(context: TenantContext | None, allowed: set[Role]) -> None:
    require_tenant_role(
        context,
        tenant_id=context.tenant_id if context else None,
        allowed=allowed,
        action="authorization.check",
    )


def require_tenant_role(
    context: TenantContext | None,
    *,
    tenant_id: str | None,
    allowed: set[Role],
    action: str,
    audit_sink: AuthorizationAuditSink | None = None,
) -> None:
    if context is None:
        _deny(
            "missing_tenant_context",
            action=action,
            request_id=None,
            tenant_id=tenant_id,
            actor=None,
            audit_sink=audit_sink,
        )
    assert context is not None
    if context.tenant_id != tenant_id:
        _deny(
            "wrong_tenant",
            action=action,
            request_id=context.request_id,
            tenant_id=tenant_id,
            actor=context.actor,
            audit_sink=audit_sink,
        )
    if not context.is_active_member:
        _deny(
            "inactive_membership",
            action=action,
            request_id=context.request_id,
            tenant_id=context.tenant_id,
            actor=context.actor,
            audit_sink=audit_sink,
        )
    if not set(context.roles).intersection(allowed):
        _deny(
            "insufficient_tenant_role",
            action=action,
            request_id=context.request_id,
            tenant_id=context.tenant_id,
            actor=context.actor,
            audit_sink=audit_sink,
        )


def require_platform_role(
    actor: ActorContext | None,
    *,
    required: PlatformRole,
    action: str,
    request_id: str,
    tenant_id: str | None = None,
    audit_sink: AuthorizationAuditSink | None = None,
) -> None:
    if actor is None or required not in actor.platform_roles:
        _deny(
            "insufficient_platform_role",
            action=action,
            request_id=request_id,
            tenant_id=tenant_id,
            actor=actor,
            audit_sink=audit_sink,
        )


def has_platform_role(platform_roles: tuple[PlatformRole, ...], role: PlatformRole) -> bool:
    return role in platform_roles


def _deny(
    reason_code: str,
    *,
    action: str,
    request_id: str | None,
    tenant_id: str | None,
    actor: ActorContext | None,
    audit_sink: AuthorizationAuditSink | None,
) -> None:
    if audit_sink is not None:
        audit_sink.record_denied(
            AuthorizationDeniedAuditRecord(
                action=action or AuditAction.AUTHORIZATION_DENIED.value,
                outcome="denied",
                request_id=request_id or "",
                actor_id=actor.actor_id if actor else None,
                tenant_id=tenant_id,
                metadata=sanitize_details({"reason": reason_code}),
            )
        )
    raise PermissionDenied(reason_code)
