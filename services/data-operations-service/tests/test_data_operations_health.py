import asyncio

import httpx
from gridlens_data_operations_service.main import app
from gridlens_db.seed import NORTHWIND_TENANT_ID


def test_health_response_body() -> None:
    async def run() -> httpx.Response:
        transport = httpx.ASGITransport(app=app)
        async with httpx.AsyncClient(transport=transport, base_url="http://test") as client:
            return await client.get("/health")

    response = asyncio.run(run())

    assert response.status_code == 200
    assert response.json() == {"status": "ok", "service": "data-operations-service"}


def test_default_app_upload_route_requires_auth() -> None:
    async def run() -> httpx.Response:
        transport = httpx.ASGITransport(app=app)
        async with httpx.AsyncClient(transport=transport, base_url="http://test") as client:
            return await client.post(f"/api/v1/tenants/{NORTHWIND_TENANT_ID}/files/upload-url")

    response = asyncio.run(run())

    assert response.status_code == 401
    assert response.json()["code"] == "authentication_required"
