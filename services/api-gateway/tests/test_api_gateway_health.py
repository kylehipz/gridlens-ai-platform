from fastapi.testclient import TestClient

from gridlens_api_gateway.main import app


def test_health_response_body() -> None:
    response = TestClient(app).get("/health")

    assert response.status_code == 200
    assert response.json() == {"status": "ok", "service": "api-gateway"}
