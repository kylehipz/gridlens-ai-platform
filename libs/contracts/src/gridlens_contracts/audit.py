from enum import StrEnum


class AuditAction(StrEnum):
    TENANT_CREATED = "tenant.created"
    TENANT_UPDATED = "tenant.updated"
    AUTHORIZATION_DENIED = "authorization.denied"
    MEMBER_INVITED = "member.invited"
    MEMBER_DEACTIVATED = "member.deactivated"
    FILE_UPLOADED = "file.uploaded"
    JOB_RETRIED = "job.retried"


def is_dotted_action(value: str) -> bool:
    left, sep, right = value.partition(".")
    return bool(left and sep and right and value == value.lower())
