import re
from collections.abc import Collection
from dataclasses import dataclass
from uuid import uuid4

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from gridlens_contracts.errors import ErrorEnvelope
from gridlens_contracts.roles import PlatformRole, Role
from starlette.types import ASGIApp, Receive, Scope, Send

from .permissions import (
    AuthorizationAuditSink,
    PermissionDenied,
    require_platform_role,
    require_tenant_role,
)
from .resolution import IdentityResolutionError, PrincipalResolver
from .tokens import (
    AuthenticationError,
    AuthMode,
    AuthSettings,
    Principal,
    TokenValidator,
    bearer_token,
)

TENANT_PATH_PATTERN = re.compile(r"^/api/v1/tenants/([^/]+)(?:/|$)")


@dataclass(frozen=True)
class AuthorizationDependencyError(Exception):
    request_id: str


class AuthenticationASGIMiddleware:
    def __init__(
        self,
        app: ASGIApp,
        *,
        settings: AuthSettings,
        validator: TokenValidator,
        resolver: PrincipalResolver | None = None,
        public_paths: Collection[str] = (),
    ) -> None:
        self.app = app
        self.settings = settings
        self.validator = validator
        self.resolver = resolver
        self.public_paths = set(public_paths)

    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        if scope["type"] != "http" or self._is_public_path(str(scope.get("path", ""))):
            await self.app(scope, receive, send)
            return

        state = scope.setdefault("state", {})
        request_id = str(state.get("request_id") or self._header(scope, "x-request-id") or uuid4().hex)
        correlation_id = str(state.get("correlation_id") or self._header(scope, "x-correlation-id") or request_id)
        state["request_id"] = request_id
        state["correlation_id"] = correlation_id

        try:
            principal = self.validator.validate(
                self._credential(scope), request_id=request_id, correlation_id=correlation_id
            )
        except AuthenticationError:
            await _safe_error_response(
                scope,
                receive,
                send,
                status_code=401,
                code="authentication_required",
                message="Authentication required.",
                request_id=request_id,
            )
            return

        tenant_id = _tenant_id_from_path(str(scope.get("path", "")))
        if self.resolver is not None:
            try:
                principal = self.resolver.resolve(
                    principal,
                    tenant_id=tenant_id,
                    request_id=request_id,
                    correlation_id=correlation_id,
                )
            except IdentityResolutionError:
                await _safe_error_response(
                    scope,
                    receive,
                    send,
                    status_code=403,
                    code="authorization_denied",
                    message="Access denied.",
                    request_id=request_id,
                )
                return

        state["principal"] = principal
        state["actor"] = principal.actor
        state["tenant_context"] = principal.tenant_context
        await self.app(scope, receive, send)

    def _is_public_path(self, path: str) -> bool:
        return path in self.public_paths

    def _credential(self, scope: Scope) -> str:
        headers = _headers_from_scope(scope)
        if self.settings.mode is AuthMode.TEST:
            test_token = headers.get(self.settings.test_auth_header.lower())
            if not test_token:
                raise AuthenticationError("Missing credentials.")
            return test_token
        return bearer_token(headers.get("authorization"))

    def _header(self, scope: Scope, name: str) -> str | None:
        return _headers_from_scope(scope).get(name)


def install_auth_middleware(
    app: FastAPI,
    *,
    settings: AuthSettings,
    validator: TokenValidator,
    resolver: PrincipalResolver | None = None,
    public_paths: Collection[str] = (),
) -> FastAPI:
    install_auth_exception_handlers(app)
    app.add_middleware(
        AuthenticationASGIMiddleware,
        settings=settings,
        validator=validator,
        resolver=resolver,
        public_paths=public_paths,
    )
    return app


def install_auth_exception_handlers(app: FastAPI) -> None:
    @app.exception_handler(AuthorizationDependencyError)
    async def authorization_dependency_error(
        request: Request, exc: AuthorizationDependencyError
    ) -> JSONResponse:
        return JSONResponse(
            status_code=403,
            content=ErrorEnvelope(
                code="authorization_denied",
                message="Access denied.",
                request_id=exc.request_id,
            ).to_dict(),
        )


def principal_from_request(request: Request) -> Principal:
    principal = getattr(request.state, "principal", None)
    if not isinstance(principal, Principal):
        raise AuthorizationDependencyError(_request_id(request))
    return principal


def require_tenant_roles(
    allowed: set[Role],
    *,
    action: str,
    audit_sink: AuthorizationAuditSink | None = None,
):
    async def dependency(request: Request) -> Principal:
        principal = principal_from_request(request)
        try:
            require_tenant_role(
                principal.tenant_context,
                tenant_id=str(request.path_params.get("tenant_id") or ""),
                allowed=allowed,
                action=action,
                audit_sink=audit_sink,
            )
        except PermissionDenied as error:
            raise AuthorizationDependencyError(_request_id(request)) from error
        return principal

    return dependency


def require_platform_roles(
    required: PlatformRole,
    *,
    action: str,
    audit_sink: AuthorizationAuditSink | None = None,
):
    async def dependency(request: Request) -> Principal:
        principal = principal_from_request(request)
        try:
            require_platform_role(
                principal.actor,
                required=required,
                action=action,
                request_id=_request_id(request),
                audit_sink=audit_sink,
            )
        except PermissionDenied as error:
            raise AuthorizationDependencyError(_request_id(request)) from error
        return principal

    return dependency


def _request_id(request: Request) -> str:
    return str(getattr(request.state, "request_id", "") or "")


def _tenant_id_from_path(path: str) -> str | None:
    match = TENANT_PATH_PATTERN.match(path)
    if match is None:
        return None
    return match.group(1)


def _headers_from_scope(scope: Scope) -> dict[str, str]:
    return {
        key.decode("latin-1").lower(): value.decode("latin-1")
        for key, value in scope.get("headers", [])
    }


async def _safe_error_response(
    scope: Scope,
    receive: Receive,
    send: Send,
    *,
    status_code: int,
    code: str,
    message: str,
    request_id: str,
) -> None:
    response = JSONResponse(
        status_code=status_code,
        content=ErrorEnvelope(code=code, message=message, request_id=request_id).to_dict(),
    )
    await response(scope, receive, send)
