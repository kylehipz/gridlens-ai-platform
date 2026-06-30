from fastapi import FastAPI
from gridlens_observability import instrument_fastapi_app

from gridlens_identity_tenant_service.api.health import router as health_router

app = FastAPI(title="GridLens Identity Tenant Service")
instrument_fastapi_app(app, service_name="identity-tenant-service")
app.include_router(health_router)
