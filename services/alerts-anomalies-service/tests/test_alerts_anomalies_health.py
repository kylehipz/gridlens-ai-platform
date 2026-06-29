from fastapi.testclient import TestClient
from gridlens_alerts_anomalies_service.main import app


def test_health_response_body() -> None:
    response = TestClient(app).get("/health")

    assert response.status_code == 200
    assert response.json() == {"status": "ok", "service": "alerts-anomalies-service"}
