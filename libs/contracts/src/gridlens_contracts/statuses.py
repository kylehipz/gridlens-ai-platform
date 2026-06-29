from enum import StrEnum


class TenantUserMembershipStatus(StrEnum):
    ACTIVE = "active"
    INVITED = "invited"
    DISABLED = "disabled"
    SUSPENDED = "suspended"
    ARCHIVED = "archived"


class FileStorageStatus(StrEnum):
    CREATED = "created"
    UPLOADING = "uploading"
    AVAILABLE = "available"
    QUARANTINED = "quarantined"
    DELETED = "deleted"
    FAILED = "failed"


class DatasetProcessingStatus(StrEnum):
    UPLOADED = "uploaded"
    QUEUED = "queued"
    VALIDATING = "validating"
    NORMALIZING = "normalizing"
    READY = "ready"
    BLOCKED = "blocked"
    FAILED = "failed"


class IngestionJobStatus(StrEnum):
    QUEUED = "queued"
    RUNNING = "running"
    COMPLETED = "completed"
    COMPLETED_WITH_ERRORS = "completed_with_errors"
    FAILED = "failed"
    CANCELLED = "cancelled"


class DataQualityStatus(StrEnum):
    PENDING = "pending"
    PASSED = "passed"
    WARNING = "warning"
    FAILED = "failed"


class BillingStatementStatus(StrEnum):
    DRAFT = "draft"
    PARSED = "parsed"
    VALIDATED = "validated"
    NEEDS_REVIEW = "needs_review"
    APPROVED = "approved"
    ARCHIVED = "archived"


class EvaluationRunStatus(StrEnum):
    QUEUED = "queued"
    RUNNING = "running"
    COMPLETED = "completed"
    COMPLETED_WITH_WARNINGS = "completed_with_warnings"
    FAILED = "failed"
    CANCELLED = "cancelled"


class EvaluationApprovalStatus(StrEnum):
    NOT_REVIEWED = "not_reviewed"
    APPROVED = "approved"
    REJECTED = "rejected"
    SUPERSEDED = "superseded"


class AlertAnomalyStatus(StrEnum):
    OPEN = "open"
    ACKNOWLEDGED = "acknowledged"
    RESOLVED = "resolved"
    DISMISSED = "dismissed"


class AssistantIndexingStatus(StrEnum):
    NOT_INDEXED = "not_indexed"
    QUEUED = "queued"
    INDEXING = "indexing"
    INDEXED = "indexed"
    FAILED = "failed"


class AssistantInteractionStatus(StrEnum):
    COMPLETED = "completed"
    REFUSED = "refused"
    FAILED = "failed"
    TIMED_OUT = "timed_out"


class ReportRunStatus(StrEnum):
    QUEUED = "queued"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"


STATUS_FAMILIES = {
    "Tenant, user, membership status": TenantUserMembershipStatus,
    "File object storage status": FileStorageStatus,
    "Dataset processing status": DatasetProcessingStatus,
    "Ingestion job status": IngestionJobStatus,
    "Data quality status": DataQualityStatus,
    "Billing statement status": BillingStatementStatus,
    "Evaluation run status": EvaluationRunStatus,
    "Evaluation approval status": EvaluationApprovalStatus,
    "Alert and anomaly status": AlertAnomalyStatus,
    "Assistant indexing status": AssistantIndexingStatus,
    "Assistant interaction status": AssistantInteractionStatus,
    "Report run status": ReportRunStatus,
}
