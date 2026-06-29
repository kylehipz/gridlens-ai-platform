from enum import StrEnum


class Role(StrEnum):
    TENANT_ADMIN = "Tenant Admin"
    ANALYST = "Analyst"
    PROGRAM_MANAGER = "Program Manager"
    AUDITOR = "Auditor"
    VIEWER = "Viewer"


class PlatformRole(StrEnum):
    PLATFORM_ADMIN = "Platform Admin"
    PLATFORM_OPERATOR = "Platform Operator"


TENANT_ROLES = tuple(role.value for role in Role)
PLATFORM_ROLES = tuple(role.value for role in PlatformRole)
