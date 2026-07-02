from typing import cast

from fastapi import FastAPI
from gridlens_auth import (
    AuthenticationError,
    AuthorizationAuditSink,
    AuthSettings,
    HttpJwksVerifier,
    IdentityRepository,
    JwksTokenValidator,
    PrincipalResolver,
    TokenValidator,
    install_auth_middleware,
)
from gridlens_db import TenantMembershipRepository
from gridlens_db.database import create_database_engine
from gridlens_observability import instrument_fastapi_app
from sqlalchemy.orm import Session

from gridlens_data_operations_service.api.health import router as health_router
from gridlens_data_operations_service.api.upload import create_upload_router


class RejectingTokenValidator:
    def validate(self, token: str, *, request_id: str, correlation_id: str):
        raise AuthenticationError("Token validation is not configured.")


def _auth_from_env() -> tuple[AuthSettings, TokenValidator, IdentityRepository] | None:
    try:
        settings = AuthSettings.from_env()
    except AuthenticationError:
        return None
    settings.require_cognito_config()
    assert settings.jwks_url is not None
    session = Session(create_database_engine())
    return (
        settings,
        JwksTokenValidator.from_settings(
            settings,
            verifier=HttpJwksVerifier(jwks_url=settings.jwks_url),
        ),
        cast(IdentityRepository, TenantMembershipRepository(session)),
    )


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
        configured_auth = _auth_from_env()
        if configured_auth is None:
            auth_settings = AuthSettings.test()
            token_validator = RejectingTokenValidator()
            resolver = None
        else:
            auth_settings, token_validator, identity_repository = configured_auth
            resolver = PrincipalResolver(identity_repository)
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
