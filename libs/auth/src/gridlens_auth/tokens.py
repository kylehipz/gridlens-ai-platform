from dataclasses import dataclass
from enum import StrEnum
from typing import Any, Protocol, Self

from gridlens_contracts.roles import PlatformRole, Role
from gridlens_contracts.tenant_context import ActorContext, TenantContext


class AuthMode(StrEnum):
    TEST = "test"
    COGNITO = "cognito"


class AuthenticationError(Exception):
    """Safe authentication failure for missing, malformed, or rejected credentials."""


@dataclass(frozen=True)
class AuthSettings:
    mode: AuthMode
    issuer: str | None = None
    audience: str | None = None
    jwks_url: str | None = None
    test_auth_header: str = "X-GridLens-Test-Auth"

    @classmethod
    def test(cls) -> Self:
        return cls(mode=AuthMode.TEST)

    @classmethod
    def cognito(cls, *, issuer: str, audience: str, jwks_url: str) -> Self:
        return cls(mode=AuthMode.COGNITO, issuer=issuer, audience=audience, jwks_url=jwks_url)

    def require_cognito_config(self) -> None:
        missing = [
            name
            for name, value in (
                ("issuer", self.issuer),
                ("audience", self.audience),
                ("jwks_url", self.jwks_url),
            )
            if not value
        ]
        if missing:
            raise AuthenticationError(
                f"Cognito authentication is missing configuration: {', '.join(missing)}"
            )


@dataclass(frozen=True)
class Principal:
    subject: str
    email: str | None
    tenant_context: TenantContext | None

    @property
    def actor(self) -> ActorContext | None:
        if self.tenant_context is None:
            return None
        return self.tenant_context.actor


class TokenValidator(Protocol):
    def validate(self, token: str, *, request_id: str, correlation_id: str) -> Principal:
        ...


class JwksVerifier(Protocol):
    def verify(self, token: str, *, issuer: str, audience: str) -> dict[str, Any]:
        ...


def bearer_token(authorization_header: str | None) -> str:
    if authorization_header is None:
        raise AuthenticationError("Missing credentials.")
    scheme, separator, token = authorization_header.partition(" ")
    if separator != " " or scheme.lower() != "bearer" or not token.strip():
        raise AuthenticationError("Invalid credentials.")
    return token.strip()


class TestTokenValidator:
    """Parse deterministic test tokens: dev:user:tenant:Role A,Role B."""

    __test__ = False

    def __init__(self, *, settings: AuthSettings | None = None):
        self.settings = settings or AuthSettings.test()

    def validate(self, token: str, *, request_id: str, correlation_id: str) -> Principal:
        if self.settings.mode is not AuthMode.TEST:
            raise AuthenticationError("Deterministic test tokens are disabled.")
        parts = token.split(":", 3)
        if len(parts) != 4 or parts[0] != "dev":
            raise AuthenticationError("Invalid deterministic test token.")
        _, subject, tenant_id, raw_roles = parts
        if not subject or not tenant_id:
            raise AuthenticationError("Invalid deterministic test token.")
        try:
            roles = tuple(Role(role.strip()) for role in raw_roles.split(",") if role.strip())
        except ValueError as error:
            raise AuthenticationError("Invalid deterministic test token.") from error
        if not roles:
            raise AuthenticationError("Invalid deterministic test token.")
        actor = ActorContext(actor_type="user", actor_id=subject, platform_roles=())
        return Principal(
            subject=subject,
            email=f"{subject}@example.test",
            tenant_context=TenantContext(
                tenant_id=tenant_id,
                actor=actor,
                roles=roles,
                membership_id=f"{tenant_id}:{subject}",
                membership_status="active",
                request_id=request_id,
                correlation_id=correlation_id,
            ),
        )


class JwksTokenValidator:
    def __init__(self, *, issuer: str, audience: str, verifier: JwksVerifier):
        self.issuer = issuer
        self.audience = audience
        self.verifier = verifier

    @classmethod
    def from_settings(cls, settings: AuthSettings, *, verifier: JwksVerifier) -> Self:
        if settings.mode is not AuthMode.COGNITO:
            raise AuthenticationError("JWKS verification requires Cognito auth mode.")
        settings.require_cognito_config()
        assert settings.issuer is not None
        assert settings.audience is not None
        return cls(issuer=settings.issuer, audience=settings.audience, verifier=verifier)

    def validate(self, token: str, *, request_id: str, correlation_id: str) -> Principal:
        try:
            claims = self.verifier.verify(token, issuer=self.issuer, audience=self.audience)
            subject = claims["sub"]
            platform_roles = tuple(PlatformRole(value) for value in claims.get("platform_roles", ()))
        except (KeyError, TypeError, ValueError) as error:
            raise AuthenticationError("Invalid JWT claims.") from error
        actor = ActorContext(
            actor_type="user",
            actor_id=subject,
            display_name=claims.get("name"),
            platform_roles=platform_roles,
        )
        tenant_id = claims.get("tenant_id")
        tenant_context = None
        if tenant_id:
            tenant_context = TenantContext(
                tenant_id=tenant_id,
                actor=actor,
                roles=self._tenant_roles(claims),
                membership_id=claims.get("membership_id"),
                membership_status=claims.get("membership_status"),
                request_id=request_id,
                correlation_id=correlation_id,
            )
        return Principal(subject=subject, email=claims.get("email"), tenant_context=tenant_context)

    def _tenant_roles(self, claims: dict[str, Any]) -> tuple[Role, ...]:
        try:
            return tuple(Role(value) for value in claims.get("tenant_roles", ()))
        except ValueError as error:
            raise AuthenticationError("Invalid JWT claims.") from error


DevTokenValidator = TestTokenValidator
