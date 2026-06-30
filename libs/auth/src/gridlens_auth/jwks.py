from importlib import import_module
from typing import Any

from .tokens import AuthenticationError


class HttpJwksVerifier:
    def __init__(self, *, jwks_url: str):
        self.jwks_url = jwks_url

    def verify(self, token: str, *, issuer: str, audience: str) -> dict[str, Any]:
        try:
            jwt = import_module("jwt")
            py_jwk_client = jwt.PyJWKClient
        except (AttributeError, ImportError) as error:
            raise AuthenticationError("JWT verification dependencies are not installed.") from error

        try:
            signing_key = py_jwk_client(self.jwks_url).get_signing_key_from_jwt(token)
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
