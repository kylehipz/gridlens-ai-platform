from dataclasses import dataclass
from typing import Any, Iterable, Protocol

from sqlalchemy import Select, select

from gridlens_db.models import app_users, tenant_memberships


class TenantOwned(Protocol):
    @property
    def id(self) -> str:
        ...

    @property
    def tenant_id(self) -> str:
        ...


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
class AppUserRecord:
    id: Any
    email: str
    display_name: str
    external_auth_provider: str
    external_subject: str
    status: str


@dataclass(frozen=True)
class MembershipRecord:
    id: Any
    tenant_id: Any
    user_id: Any
    role: str
    status: str


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

    def get_user_by_external_identity(self, provider: str, subject: str) -> AppUserRecord | None:
        statement = app_user_external_identity_statement(provider, subject)
        row = self._session.execute(statement).mappings().one_or_none()
        if row is None:
            return None
        return _app_user_from_mapping(row)

    def get_membership_for_user_tenant(self, *, user_id: Any, tenant_id: Any) -> MembershipRecord | None:
        statement = membership_user_tenant_statement(user_id=user_id, tenant_id=tenant_id)
        row = self._session.execute(statement).mappings().one_or_none()
        if row is None:
            return None
        return _membership_from_mapping(row)


def membership_lookup_statement(tenant_id: Any, membership_id: Any) -> Select[Any]:
    return select(tenant_memberships).where(
        tenant_memberships.c.tenant_id == tenant_id,
        tenant_memberships.c.id == membership_id,
    )


def app_user_external_identity_statement(provider: str, subject: str) -> Select[Any]:
    return select(app_users).where(
        app_users.c.external_auth_provider == provider,
        app_users.c.external_subject == subject,
    )


def membership_user_tenant_statement(*, user_id: Any, tenant_id: Any) -> Select[Any]:
    return select(tenant_memberships).where(
        tenant_memberships.c.user_id == user_id,
        tenant_memberships.c.tenant_id == tenant_id,
    )


def _app_user_from_mapping(row: Any) -> AppUserRecord:
    return AppUserRecord(
        id=row["id"],
        email=row["email"],
        display_name=row["display_name"],
        external_auth_provider=row["external_auth_provider"],
        external_subject=row["external_subject"],
        status=row["status"],
    )


def _membership_from_mapping(row: Any) -> MembershipRecord:
    return MembershipRecord(
        id=row["id"],
        tenant_id=row["tenant_id"],
        user_id=row["user_id"],
        role=row["role"],
        status=row["status"],
    )
