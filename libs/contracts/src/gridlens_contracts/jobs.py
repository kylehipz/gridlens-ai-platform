from dataclasses import dataclass
from datetime import datetime

from .statuses import IngestionJobStatus, ReportRunStatus


@dataclass(frozen=True)
class JobReference:
    job_id: str
    tenant_id: str
    status: IngestionJobStatus | ReportRunStatus
    attempt_number: int
    created_at: datetime
