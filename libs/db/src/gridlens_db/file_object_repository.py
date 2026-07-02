from dataclasses import dataclass
from typing import Any

from sqlalchemy import Select, select

from gridlens_db.models import file_objects


@dataclass(frozen=True)
class FileObjectRecord:
    id: Any
    tenant_id: Any
    created_by_user_id: Any
    object_purpose: str
    original_file_name: str
    content_type: str
    storage_bucket: str
    storage_key: str
    checksum_sha256: str
    file_size_bytes: int
    storage_status: str


class FileObjectRepository:
    def __init__(self, session: Any):
        self._session = session

    def list_for_tenant(self, tenant_id: Any) -> list[FileObjectRecord]:
        statement = (
            select(file_objects)
            .where(file_objects.c.tenant_id == tenant_id)
            .order_by(file_objects.c.created_at, file_objects.c.id)
        )
        return [_file_object_from_mapping(row) for row in self._session.execute(statement).mappings().all()]

    def get_for_tenant(self, tenant_id: Any, file_object_id: Any) -> FileObjectRecord:
        statement = file_object_lookup_statement(tenant_id, file_object_id)
        row = self._session.execute(statement).mappings().one_or_none()
        if row is None:
            raise LookupError("File object not found.")
        return _file_object_from_mapping(row)


def file_object_lookup_statement(tenant_id: Any, file_object_id: Any) -> Select[Any]:
    return select(file_objects).where(
        file_objects.c.tenant_id == tenant_id,
        file_objects.c.id == file_object_id,
    )


def _file_object_from_mapping(row: Any) -> FileObjectRecord:
    return FileObjectRecord(
        id=row["id"],
        tenant_id=row["tenant_id"],
        created_by_user_id=row["created_by_user_id"],
        object_purpose=row["object_purpose"],
        original_file_name=row["original_file_name"],
        content_type=row["content_type"],
        storage_bucket=row["storage_bucket"],
        storage_key=row["storage_key"],
        checksum_sha256=row["checksum_sha256"],
        file_size_bytes=row["file_size_bytes"],
        storage_status=row["storage_status"],
    )
