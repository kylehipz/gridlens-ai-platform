from dataclasses import dataclass


@dataclass(frozen=True)
class TenantFixture:
    id: str
    name: str
    slug: str


@dataclass(frozen=True)
class UserFixture:
    id: str
    email: str
    tenant_id: str
    role: str
    membership_status: str = "active"


def make_tenant(slug: str) -> TenantFixture:
    return TenantFixture(id=f"{slug}_id", name=slug.replace("_", " ").title(), slug=slug)


def make_user(name: str, tenant: TenantFixture, *, role: str) -> UserFixture:
    return UserFixture(
        id=f"{tenant.slug}_{name}_id",
        email=f"{name}@{tenant.slug}.example.test",
        tenant_id=tenant.id,
        role=role,
    )
