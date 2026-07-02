import unittest
from types import SimpleNamespace
from unittest.mock import patch

from gridlens_auth import AuthenticationError, HttpJwksVerifier


class FakeSigningKey:
    key = "public-key"


class FakePyJWKClient:
    instances = []

    def __init__(self, jwks_url: str):
        self.jwks_url = jwks_url
        self.tokens = []
        self.__class__.instances.append(self)

    def get_signing_key_from_jwt(self, token: str) -> FakeSigningKey:
        self.tokens.append(token)
        return FakeSigningKey()


class FakeJwtModule:
    PyJWKClient = FakePyJWKClient

    def __init__(self):
        self.decode_calls = []

    def decode(self, token, key, *, algorithms, audience, issuer):
        self.decode_calls.append(
            {
                "token": token,
                "key": key,
                "algorithms": algorithms,
                "audience": audience,
                "issuer": issuer,
            }
        )
        return {"sub": token}


class HttpJwksVerifierTests(unittest.TestCase):
    def setUp(self) -> None:
        FakePyJWKClient.instances = []

    def test_reuses_jwk_client_across_verifications(self):
        jwt_module = FakeJwtModule()
        verifier = HttpJwksVerifier(jwks_url="https://issuer.example.test/jwks.json")

        with patch("gridlens_auth.jwks.import_module", return_value=jwt_module) as import_module:
            first = verifier.verify("jwt_1", issuer="https://issuer.example.test", audience="gridlens")
            second = verifier.verify("jwt_2", issuer="https://issuer.example.test", audience="gridlens")

        self.assertEqual({"sub": "jwt_1"}, first)
        self.assertEqual({"sub": "jwt_2"}, second)
        self.assertEqual(1, import_module.call_count)
        self.assertEqual(1, len(FakePyJWKClient.instances))
        self.assertEqual("https://issuer.example.test/jwks.json", FakePyJWKClient.instances[0].jwks_url)
        self.assertEqual(["jwt_1", "jwt_2"], FakePyJWKClient.instances[0].tokens)
        self.assertEqual(
            [
                {
                    "token": "jwt_1",
                    "key": "public-key",
                    "algorithms": ["RS256"],
                    "audience": "gridlens",
                    "issuer": "https://issuer.example.test",
                },
                {
                    "token": "jwt_2",
                    "key": "public-key",
                    "algorithms": ["RS256"],
                    "audience": "gridlens",
                    "issuer": "https://issuer.example.test",
                },
            ],
            jwt_module.decode_calls,
        )

    def test_missing_pyjwt_dependency_maps_to_authentication_error(self):
        verifier = HttpJwksVerifier(jwks_url="https://issuer.example.test/jwks.json")

        with patch("gridlens_auth.jwks.import_module", side_effect=ImportError):
            with self.assertRaises(AuthenticationError):
                verifier.verify("jwt", issuer="https://issuer.example.test", audience="gridlens")

    def test_missing_jwk_client_maps_to_authentication_error(self):
        verifier = HttpJwksVerifier(jwks_url="https://issuer.example.test/jwks.json")

        with patch("gridlens_auth.jwks.import_module", return_value=SimpleNamespace()):
            with self.assertRaises(AuthenticationError):
                verifier.verify("jwt", issuer="https://issuer.example.test", audience="gridlens")


if __name__ == "__main__":
    unittest.main()
