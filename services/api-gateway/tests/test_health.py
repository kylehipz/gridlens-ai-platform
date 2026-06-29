from http import HTTPStatus
import json
import sys
from pathlib import Path
from unittest import TestCase

sys.path.append(str(Path(__file__).resolve().parents[1] / "src"))

from gridlens_api_gateway.main import HealthHandler


class FakeRequest:
    def makefile(self, *_args, **_kwargs):
        raise NotImplementedError


class HealthHandlerTests(TestCase):
    def test_health_response_body(self) -> None:
        handler = object.__new__(HealthHandler)
        handler.path = "/health"
        handler.request_version = "HTTP/1.1"
        handler.command = "GET"
        handler.close_connection = False
        handler.requestline = "GET /health HTTP/1.1"
        handler.responses = []
        handler.headers = []
        handler.body = bytearray()
        handler.wfile = handler

        handler.send_response = lambda code, message=None: handler.responses.append(code)
        handler.send_header = lambda key, value: handler.headers.append((key, value))
        handler.end_headers = lambda: None
        handler.write = lambda payload: handler.body.extend(payload)

        handler.do_GET()

        self.assertEqual(handler.responses, [HTTPStatus.OK])
        self.assertEqual(
            json.loads(bytes(handler.body)),
            {"status": "ok", "service": "api-gateway"},
        )
