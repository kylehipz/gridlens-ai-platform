from fastapi import FastAPI
from gridlens_auth import (
    AuthenticationError,
    AuthorizationAuditSink,
    AuthSettings,
    IdentityRepository,
    PrincipalResolver,
    TokenValidator,
    install_auth_middleware,
)
from gridlens_observability import instrument_fastapi_app

from gridlens_data_operations_service.api.health import router as health_router
from gridlens_data_operations_service.api.upload import create_upload_router


class RejectingTokenValidator:
    def validate(self, token: str, *, request_id: str, correlation_id: str):
        raise AuthenticationError("Token validation is not configured.")


def create_app(
    *,
    auth_settings: AuthSettings | None = None,
    token_validator: TokenValidator | None = None,
    identity_repository: IdentityRepository | None = None,
    audit_sink: AuthorizationAuditSink | None = None,
) -> FastAPI:
    app = FastAPI(title="GridLens Data Operations Service")
    app.include_router(health_router)
    app.include_router(create_upload_router(audit_sink=audit_sink))
    if auth_settings is None or token_validator is None or identity_repository is None:
        auth_settings = AuthSettings.test()
        token_validator = RejectingTokenValidator()
        resolver = None
    else:
        resolver = PrincipalResolver(identity_repository)
    if auth_settings is not None and token_validator is not None:
        install_auth_middleware(
            app,
            settings=auth_settings,
            validator=token_validator,
            resolver=resolver,
            public_paths={"/health", "/healthz"},
        )
    instrument_fastapi_app(app, service_name="data-operations-service")
    return app


app = create_app()
