import json
from http import HTTPStatus
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

from fastapi import FastAPI

from gridlens_api_gateway.config import load_settings

app = FastAPI(title="GridLens API Gateway Support Service")


class HealthHandler(BaseHTTPRequestHandler):
    server_version = "GridLensScaffoldAPI/0.1"

    def do_GET(self) -> None:
        if self.path not in {"/health", "/healthz"}:
            self.send_error(HTTPStatus.NOT_FOUND, "not found")
            return

        body = json.dumps({"status": "ok", "service": "api-gateway"}).encode()
        self.send_response(HTTPStatus.OK)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def log_message(self, format: str, *args: object) -> None:
        return


def create_server() -> ThreadingHTTPServer:
    settings = load_settings()
    return ThreadingHTTPServer((settings.host, settings.port), HealthHandler)


def main() -> None:
    server = create_server()
    try:
        server.serve_forever()
    finally:
        server.server_close()


if __name__ == "__main__":
    main()
