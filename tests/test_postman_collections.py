import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
COLLECTION = ROOT / "postman" / "gridlens-local.postman_collection.json"


def _walk_items(items: list[dict]) -> list[dict]:
    requests = []
    for item in items:
        if "request" in item:
            requests.append(item)
        requests.extend(_walk_items(item.get("item", [])))
    return requests


def test_gridlens_local_collection_is_postman_v21() -> None:
    collection = json.loads(COLLECTION.read_text())

    assert collection["info"]["schema"] == (
        "https://schema.getpostman.com/json/collection/v2.1.0/collection.json"
    )
    assert collection["info"]["name"] == "GridLens Local API"


def test_gridlens_local_collection_covers_health_requests() -> None:
    collection = json.loads(COLLECTION.read_text())
    requests = _walk_items(collection["item"])
    request_names = {request["name"] for request in requests}
    variable_names = {variable["key"] for variable in collection["variable"]}

    assert "Health" in request_names
    assert "Unknown Route" in request_names
    assert "Observability Smoke" in request_names
    assert "Observability Controlled Failure" in request_names
    assert "Identity Tenant Service Health" in request_names
    assert "Alerts Anomalies Service Health" in request_names
    assert "base_url" in variable_names
    assert "observability_trace_id" in variable_names
    assert "identity_tenant_service_url" in variable_names
    assert "alerts_anomalies_service_url" in variable_names
    assert "api_gateway_service_url" not in variable_names
