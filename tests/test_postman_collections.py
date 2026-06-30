import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
COLLECTION = ROOT / "postman" / "gridlens-local.postman_collection.json"
ENVIRONMENT = ROOT / "postman" / "gridlens-local.postman_environment.json"


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
    assert "Create Upload URL" in request_names
    assert "Unknown Route" in request_names
    assert "Observability Smoke" in request_names
    assert "Observability Controlled Failure" in request_names
    assert "Identity Tenant Service Health" in request_names
    assert "Alerts Anomalies Service Health" in request_names
    assert "base_url" in variable_names
    assert "access_token" in variable_names
    assert "northwind_tenant_id" in variable_names
    assert "cascade_tenant_id" in variable_names
    assert "cognito_authorization_url" in variable_names
    assert "cognito_token_url" in variable_names
    assert "cognito_client_id" in variable_names
    assert "cognito_redirect_uri" in variable_names
    assert "cognito_scopes" in variable_names
    assert "observability_trace_id" in variable_names
    assert "identity_tenant_service_url" in variable_names
    assert "alerts_anomalies_service_url" in variable_names
    assert "api_gateway_service_url" not in variable_names


def test_gridlens_local_environment_has_defaults_and_descriptions() -> None:
    collection = json.loads(COLLECTION.read_text())
    environment = json.loads(ENVIRONMENT.read_text())
    collection_variable_names = {variable["key"] for variable in collection["variable"]}
    environment_values = {value["key"]: value for value in environment["values"]}

    assert environment["name"] == "GridLens Local"
    assert collection_variable_names <= set(environment_values)
    assert environment_values["base_url"]["value"] == "http://127.0.0.1:8000"
    assert environment_values["tenant_id"]["value"] == "10000000-0000-4000-8000-000000000001"
    assert environment_values["northwind_tenant_id"]["value"] == "10000000-0000-4000-8000-000000000001"
    assert environment_values["cascade_tenant_id"]["value"] == "10000000-0000-4000-8000-000000000002"
    assert environment_values["user_id"]["value"] == "20000000-0000-4000-8000-000000000001"
    assert environment_values["access_token"]["type"] == "secret"
    assert environment_values["cognito_client_id"]["description"]

    for value in environment_values.values():
        if value["value"] == "":
            assert value.get("description")
