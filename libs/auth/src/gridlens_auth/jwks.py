from importlib import import_module
from typing import Any

from .tokens import AuthenticationError


class HttpJwksVerifier:
    def __init__(self, *, jwks_url: str):
        self.jwks_url = jwks_url
        self._jwt_module: Any | None = None
        self._jwk_client: Any | None = None

    def verify(self, token: str, *, issuer: str, audience: str) -> dict[str, Any]:
        jwt = self._jwt()
        try:
            signing_key = self._client().get_signing_key_from_jwt(token)
            claims = jwt.decode(
                token,
                signing_key.key,
                algorithms=["RS256"],
                audience=audience,
                issuer=issuer,
            )
        except Exception as error:
            raise AuthenticationError("JWT verification failed.") from error
        if not isinstance(claims, dict):
            raise AuthenticationError("JWT verification failed.")
        return claims

    def _jwt(self) -> Any:
        if self._jwt_module is not None:
            return self._jwt_module
        try:
            jwt = import_module("jwt")
        except (AttributeError, ImportError) as error:
            raise AuthenticationError("JWT verification dependencies are not installed.") from error
        self._jwt_module = jwt
        return jwt

    def _client(self) -> Any:
        if self._jwk_client is not None:
            return self._jwk_client
        jwt = self._jwt()
        try:
            self._jwk_client = jwt.PyJWKClient(self.jwks_url)
        except AttributeError as error:
            raise AuthenticationError("JWT verification dependencies are not installed.") from error
        return self._jwk_client
