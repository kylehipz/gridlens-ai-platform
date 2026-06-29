from dataclasses import dataclass, field

from .roles import PlatformRole, Role


@dataclass(frozen=True)
class ActorContext:
    actor_type: str
    actor_id: str
    display_name: str | None = None
    platform_roles: tuple[PlatformRole, ...] = ()

    @classmethod
    def system(cls, service: str) -> "ActorContext":
        return cls(actor_type="system", actor_id=service, display_name=service)


@dataclass(frozen=True)
class TenantContext:
    tenant_id: str
    actor: ActorContext
    request_id: str
    correlation_id: str
    roles: tuple[Role, ...] = field(default_factory=tuple)
    membership_id: str | None = None
    membership_status: str | None = None

    @property
    def is_active_member(self) -> bool:
        return self.membership_status == "active"
