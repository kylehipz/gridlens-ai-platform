from gridlens_contracts.roles import PlatformRole, Role
from gridlens_contracts.tenant_context import TenantContext


class PermissionDenied(Exception):
    pass


def require_role(context: TenantContext | None, allowed: set[Role]) -> None:
    if context is None:
        raise PermissionDenied("Missing tenant context.")
    if not context.is_active_member:
        raise PermissionDenied("Inactive tenant membership.")
    if not set(context.roles).intersection(allowed):
        raise PermissionDenied("Role is not permitted.")


def has_platform_role(platform_roles: tuple[PlatformRole, ...], role: PlatformRole) -> bool:
    return role in platform_roles
