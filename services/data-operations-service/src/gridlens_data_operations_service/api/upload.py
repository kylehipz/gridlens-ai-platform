from typing import Annotated

from fastapi import APIRouter, Depends, Request
from gridlens_auth import (
    AuthorizationAuditSink,
    Principal,
    require_tenant_roles,
)
from gridlens_contracts.roles import Role


def create_upload_router(*, audit_sink: AuthorizationAuditSink | None = None) -> APIRouter:
    router = APIRouter(prefix="/api/v1/tenants/{tenant_id}/files", tags=["files"])
    authorize_upload = require_tenant_roles(
        {Role.ANALYST, Role.TENANT_ADMIN},
        action="files.upload_url.create",
        audit_sink=audit_sink,
    )

    @router.post("/upload-url")
    async def create_upload_url(
        tenant_id: str,
        request: Request,
        principal: Annotated[Principal, Depends(authorize_upload)],
    ) -> dict[str, object]:
        return {
            "status": "authorized",
            "tenant_id": tenant_id,
            "actor_user_id": principal.user_id,
            "request_id": request.state.request_id,
            "correlation_id": request.state.correlation_id,
            "upload": {
                "authorized": True,
                "storage": "deferred",
            },
        }

    return router
