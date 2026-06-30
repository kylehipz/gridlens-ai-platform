from dataclasses import dataclass
from typing import Any, Iterable, Protocol

from sqlalchemy import Select, select, text

from gridlens_db.models import file_objects, tenant_memberships


class TenantOwned(Protocol):
    @property
    def id(self) -> str:
        ...

    @property
    def tenant_id(self) -> str:
        ...


@dataclass(frozen=True)
class RlsSessionContext:
    tenant_id: str
    actor_id: str
    request_id: str

    def settings(self) -> dict[str, str]:
        return {
            "app.tenant_id": self.tenant_id,
            "app.actor_id": self.actor_id,
            "app.request_id": self.request_id,
        }

    def apply(self, connection: Any) -> None:
        for key, value in self.settings().items():
            connection.execute(
                text("select set_config(:key, :value, true)"),
                {"key": key, "value": value},
            )


class TenantScopedRepository:
    def __init__(self, records: Iterable[TenantOwned]):
        self._records = list(records)

    def list_for_tenant(self, tenant_id: str) -> list[TenantOwned]:
        return [record for record in self._records if record.tenant_id == tenant_id]

    def get_for_tenant(self, tenant_id: str, record_id: str) -> TenantOwned:
        for record in self._records:
            if record.id == record_id and record.tenant_id == tenant_id:
                return record
        raise LookupError("Tenant-scoped record not found.")


@dataclass(frozen=True)
class MembershipRecord:
    id: Any
    tenant_id: Any
    user_id: Any
    role: str
    status: str


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


class TenantMembershipRepository:
    def __init__(self, session: Any):
        self._session = session

    def list_for_tenant(self, tenant_id: Any) -> list[MembershipRecord]:
        statement = (
            select(tenant_memberships)
            .where(tenant_memberships.c.tenant_id == tenant_id)
            .order_by(tenant_memberships.c.created_at, tenant_memberships.c.id)
        )
        return [_membership_from_mapping(row) for row in self._session.execute(statement).mappings().all()]

    def get_for_tenant(self, tenant_id: Any, membership_id: Any) -> MembershipRecord:
        statement = membership_lookup_statement(tenant_id, membership_id)
        row = self._session.execute(statement).mappings().one_or_none()
        if row is None:
            raise LookupError("Tenant membership not found.")
        return _membership_from_mapping(row)


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


def membership_lookup_statement(tenant_id: Any, membership_id: Any) -> Select[Any]:
    return select(tenant_memberships).where(
        tenant_memberships.c.tenant_id == tenant_id,
        tenant_memberships.c.id == membership_id,
    )


def file_object_lookup_statement(tenant_id: Any, file_object_id: Any) -> Select[Any]:
    return select(file_objects).where(
        file_objects.c.tenant_id == tenant_id,
        file_objects.c.id == file_object_id,
    )


def _membership_from_mapping(row: Any) -> MembershipRecord:
    return MembershipRecord(
        id=row["id"],
        tenant_id=row["tenant_id"],
        user_id=row["user_id"],
        role=row["role"],
        status=row["status"],
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
