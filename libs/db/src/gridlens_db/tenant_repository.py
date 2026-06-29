from dataclasses import dataclass
from typing import Iterable, Protocol


class TenantOwned(Protocol):
    id: str
    tenant_id: str


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
