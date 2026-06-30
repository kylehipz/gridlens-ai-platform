import asyncio
from dataclasses import replace

import httpx
from gridlens_auth import (
    AppUserRecord,
    AuthorizationDeniedAuditRecord,
    AuthSettings,
    TenantMembershipRecord,
    TestTokenValidator,
)
from gridlens_data_operations_service.main import create_app
from gridlens_db.seed import CASCADE_TENANT_ID, JORDAN_USER_ID, NORTHWIND_TENANT_ID


class FakeIdentityRepository:
    def __init__(self):
        self.user = AppUserRecord(
            id=str(JORDAN_USER_ID),
            email="jordan.lee@example.com",
            display_name="Jordan Lee",
            external_auth_provider="cognito",
            external_subject="dev-jordan-lee",
            status="active",
        )
        self.memberships = {
            str(NORTHWIND_TENANT_ID): TenantMembershipRecord(
                id="30000000-0000-4000-8000-000000000001",
                tenant_id=str(NORTHWIND_TENANT_ID),
                user_id=str(JORDAN_USER_ID),
                role="Analyst",
                status="active",
            ),
            str(CASCADE_TENANT_ID): TenantMembershipRecord(
                id="30000000-0000-4000-8000-000000000002",
                tenant_id=str(CASCADE_TENANT_ID),
                user_id=str(JORDAN_USER_ID),
                role="Viewer",
                status="active",
            ),
        }

    def get_user_by_external_identity(self, provider: str, subject: str):
        if provider == "cognito" and subject == self.user.external_subject:
            return self.user
        return None

    def get_membership_for_user_tenant(self, *, user_id: str, tenant_id: str):
        membership = self.memberships.get(tenant_id)
        if membership and membership.user_id == user_id:
            return membership
        return None


class FakeAuditSink:
    def __init__(self):
        self.records: list[AuthorizationDeniedAuditRecord] = []

    def record_denied(self, record: AuthorizationDeniedAuditRecord) -> None:
        self.records.append(record)


def build_app(repository: FakeIdentityRepository | None = None, audit_sink: FakeAuditSink | None = None):
    settings = AuthSettings.test()
    return create_app(
        auth_settings=settings,
        token_validator=TestTokenValidator(settings=settings),
        identity_repository=repository or FakeIdentityRepository(),
        audit_sink=audit_sink,
    )


def run_request(app, request):
    async def run():
        transport = httpx.ASGITransport(app=app)
        async with httpx.AsyncClient(transport=transport, base_url="http://test") as client:
            return await request(client)

    return asyncio.run(run())


def test_northwind_analyst_can_request_upload_placeholder() -> None:
    response = run_request(
        build_app(),
        lambda client: client.post(
            f"/api/v1/tenants/{NORTHWIND_TENANT_ID}/files/upload-url",
            headers={
                "X-GridLens-Test-Auth": "dev:dev-jordan-lee:ignored:Viewer",
                "X-Request-ID": "req_northwind",
            },
        ),
    )

    assert response.status_code == 200
    assert response.json() == {
        "status": "authorized",
        "tenant_id": str(NORTHWIND_TENANT_ID),
        "actor_user_id": str(JORDAN_USER_ID),
        "request_id": "req_northwind",
        "correlation_id": "req_northwind",
        "upload": {
            "authorized": True,
            "storage": "deferred",
        },
    }


def test_missing_auth_receives_401_before_upload_route() -> None:
    response = run_request(
        build_app(),
        lambda client: client.post(
            f"/api/v1/tenants/{NORTHWIND_TENANT_ID}/files/upload-url",
            headers={"X-Request-ID": "req_missing"},
        ),
    )

    assert response.status_code == 401
    assert response.json() == {
        "code": "authentication_required",
        "message": "Authentication required.",
        "request_id": "req_missing",
    }


def test_cascade_viewer_receives_403_and_denied_audit() -> None:
    sink = FakeAuditSink()
    response = run_request(
        build_app(audit_sink=sink),
        lambda client: client.post(
            f"/api/v1/tenants/{CASCADE_TENANT_ID}/files/upload-url",
            headers={
                "X-GridLens-Test-Auth": "dev:dev-jordan-lee:ignored:Analyst",
                "X-Request-ID": "req_cascade",
            },
        ),
    )

    assert response.status_code == 403
    assert response.json() == {
        "code": "authorization_denied",
        "message": "Access denied.",
        "request_id": "req_cascade",
    }
    assert len(sink.records) == 1
    assert sink.records[0].actor_id == str(JORDAN_USER_ID)
    assert sink.records[0].tenant_id == str(CASCADE_TENANT_ID)
    assert sink.records[0].action == "files.upload_url.create"
    assert sink.records[0].outcome == "denied"
    assert sink.records[0].request_id == "req_cascade"
    assert sink.records[0].metadata == {"reason": "insufficient_tenant_role"}


def test_wrong_tenant_returns_safe_403_without_forbidden_names() -> None:
    repository = FakeIdentityRepository()
    repository.memberships[str(NORTHWIND_TENANT_ID)] = replace(
        repository.memberships[str(NORTHWIND_TENANT_ID)],
        status="disabled",
    )
    response = run_request(
        build_app(repository=repository),
        lambda client: client.post(
            f"/api/v1/tenants/{NORTHWIND_TENANT_ID}/files/upload-url",
            headers={
                "X-GridLens-Test-Auth": "dev:dev-jordan-lee:ignored:Analyst",
                "X-Request-ID": "req_wrong",
            },
        ),
    )

    body = response.text
    assert response.status_code == 403
    assert response.json() == {
        "code": "authorization_denied",
        "message": "Access denied.",
        "request_id": "req_wrong",
    }
    assert "Northwind" not in body
    assert "Cascade" not in body
    assert "northwind-meter-readings" not in body
    assert "cascade-program-guide" not in body
