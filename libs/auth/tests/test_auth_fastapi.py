import asyncio
from typing import Annotated

import httpx
from fastapi import Depends, FastAPI, Request
from gridlens_auth import (
    AppUserRecord,
    AuthSettings,
    PlatformRoleAssignmentRecord,
    Principal,
    PrincipalResolver,
    TenantMembershipRecord,
    TestTokenValidator,
    install_auth_middleware,
    require_platform_roles,
    require_tenant_roles,
)
from gridlens_auth.permissions import AuthorizationDeniedAuditRecord
from gridlens_contracts.roles import PlatformRole, Role
from gridlens_observability import instrument_fastapi_app


class FakeIdentityRepository:
    def __init__(self):
        self.user = AppUserRecord(
            id="user_1",
            email="user@example.test",
            display_name="Test User",
            external_auth_provider="cognito",
            external_subject="user_1",
            status="active",
        )
        self.membership = TenantMembershipRecord(
            id="membership_1",
            tenant_id="tenant_northwind",
            user_id="user_1",
            role="Analyst",
            status="active",
        )
        self.platform_roles = [PlatformRole.PLATFORM_ADMIN]
        self.user_calls = 0
        self.membership_calls = 0
        self.platform_role_calls = 0

    def get_user_by_external_identity(self, provider: str, subject: str) -> AppUserRecord | None:
        self.user_calls += 1
        if provider == "cognito" and subject == self.user.external_subject:
            return self.user
        return None

    def list_active_platform_roles_for_user(
        self, user_id: str
    ) -> list[PlatformRoleAssignmentRecord]:
        self.platform_role_calls += 1
        if user_id == self.user.id:
            return [
                PlatformRoleAssignmentRecord(
                    id=f"platform-role-{index}",
                    user_id=user_id,
                    role=role.value,
                    status="active",
                )
                for index, role in enumerate(self.platform_roles, start=1)
            ]
        return []

    def get_membership_for_user_tenant(
        self, *, user_id: str, tenant_id: str
    ) -> TenantMembershipRecord | None:
        self.membership_calls += 1
        if user_id == self.membership.user_id and tenant_id == self.membership.tenant_id:
            return self.membership
        return None


class FakeAuditSink:
    def __init__(self):
        self.records: list[AuthorizationDeniedAuditRecord] = []

    def record_denied(self, record: AuthorizationDeniedAuditRecord) -> None:
        self.records.append(record)


def run_request(app: FastAPI, request):
    async def run():
        transport = httpx.ASGITransport(app=app)
        async with httpx.AsyncClient(transport=transport, base_url="http://test") as client:
            return await request(client)

    return asyncio.run(run())


def build_app(*, audit_sink: FakeAuditSink | None = None):
    app = FastAPI()
    repo = FakeIdentityRepository()
    handler_calls = {"protected": 0}
    upload_authorization = require_tenant_roles(
        {Role.ANALYST, Role.TENANT_ADMIN},
        action="files.upload_url.create",
        audit_sink=audit_sink,
    )
    platform_authorization = require_platform_roles(
        PlatformRole.PLATFORM_ADMIN,
        action="tenants.create",
        audit_sink=audit_sink,
    )

    @app.get("/health")
    async def health() -> dict[str, str]:
        return {"status": "ok"}

    @app.post("/api/v1/tenants/{tenant_id}/files/upload-url")
    async def upload_url(
        request: Request,
        principal: Annotated[Principal, Depends(upload_authorization)],
    ) -> dict[str, str | int | None]:
        handler_calls["protected"] += 1
        return {
            "subject": principal.subject,
            "user_id": principal.user_id,
            "request_id": request.state.request_id,
            "correlation_id": request.state.correlation_id,
            "handler_calls": handler_calls["protected"],
        }

    @app.post("/api/v1/tenants")
    async def create_tenant(
        principal: Annotated[Principal, Depends(platform_authorization)],
    ) -> dict[str, str | None]:
        handler_calls["protected"] += 1
        return {
            "subject": principal.subject,
            "user_id": principal.user_id,
            "actor_id": principal.actor.actor_id if principal.actor else None,
        }

    install_auth_middleware(
        app,
        settings=AuthSettings.test(),
        validator=TestTokenValidator(settings=AuthSettings.test()),
        resolver=PrincipalResolver(repo),
        public_paths={"/health"},
    )
    instrument_fastapi_app(app, service_name="auth-test-service")
    return app, repo, handler_calls


def test_public_allowlisted_route_skips_authentication() -> None:
    app, repo, _handler_calls = build_app()

    response = run_request(app, lambda client: client.get("/health"))

    assert response.status_code == 200
    assert response.json() == {"status": "ok"}
    assert repo.user_calls == 0


def test_protected_route_blocks_missing_credentials_before_handler() -> None:
    app, _repo, handler_calls = build_app()

    response = run_request(
        app,
        lambda client: client.post(
            "/api/v1/tenants/tenant_northwind/files/upload-url",
            headers={"X-Request-ID": "req_missing"},
        ),
    )

    assert response.status_code == 401
    assert response.json() == {
        "code": "authentication_required",
        "message": "Authentication required.",
        "request_id": "req_missing",
    }
    assert handler_calls["protected"] == 0


def test_valid_credentials_attach_resolved_state_and_reuse_observability_ids() -> None:
    app, repo, handler_calls = build_app()

    response = run_request(
        app,
        lambda client: client.post(
            "/api/v1/tenants/tenant_northwind/files/upload-url",
            headers={
                "X-GridLens-Test-Auth": "dev:user_1:ignored:Viewer",
                "X-Request-ID": "req_1",
                "X-Correlation-ID": "corr_1",
            },
        ),
    )

    assert response.status_code == 200
    assert response.json() == {
        "subject": "user_1",
        "user_id": "user_1",
        "request_id": "req_1",
        "correlation_id": "corr_1",
        "handler_calls": 1,
    }
    assert repo.user_calls == 1
    assert repo.platform_role_calls == 1
    assert repo.membership_calls == 1
    assert handler_calls["protected"] == 1


def test_platform_route_authorizes_from_gridlens_roles_without_tenant_context() -> None:
    app, repo, handler_calls = build_app()

    response = run_request(
        app,
        lambda client: client.post(
            "/api/v1/tenants",
            headers={
                "X-GridLens-Test-Auth": "dev:user_1:ignored:Viewer",
                "X-Request-ID": "req_platform",
            },
        ),
    )

    assert response.status_code == 200
    assert response.json() == {
        "subject": "user_1",
        "user_id": "user_1",
        "actor_id": "user_1",
    }
    assert repo.user_calls == 1
    assert repo.platform_role_calls == 1
    assert repo.membership_calls == 0
    assert handler_calls["protected"] == 1


def test_authorization_dependency_denies_without_revalidating_token() -> None:
    sink = FakeAuditSink()
    app, repo, handler_calls = build_app(audit_sink=sink)

    response = run_request(
        app,
        lambda client: client.post(
            "/api/v1/tenants/tenant_northwind/files/upload-url",
            headers={
                "X-GridLens-Test-Auth": "dev:user_1:ignored:Viewer",
                "X-Request-ID": "req_denied",
            },
        ),
    )

    assert response.status_code == 200

    repo.membership = TenantMembershipRecord(
        id="membership_1",
        tenant_id="tenant_northwind",
        user_id="user_1",
        role="Viewer",
        status="active",
    )
    response = run_request(
        app,
        lambda client: client.post(
            "/api/v1/tenants/tenant_northwind/files/upload-url",
            headers={
                "X-GridLens-Test-Auth": "dev:user_1:ignored:Analyst",
                "X-Request-ID": "req_denied",
            },
        ),
    )

    assert response.status_code == 403
    assert response.json() == {
        "code": "authorization_denied",
        "message": "Access denied.",
        "request_id": "req_denied",
    }
    assert handler_calls["protected"] == 1
    assert repo.user_calls == 2
    assert repo.membership_calls == 2
    assert sink.records[0].actor_id == "user_1"
    assert sink.records[0].tenant_id == "tenant_northwind"
    assert sink.records[0].action == "files.upload_url.create"
    assert sink.records[0].outcome == "denied"
    assert sink.records[0].request_id == "req_denied"
    assert sink.records[0].metadata == {"reason": "insufficient_tenant_role"}
