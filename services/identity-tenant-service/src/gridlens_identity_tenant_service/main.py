from fastapi import FastAPI

from gridlens_identity_tenant_service.api.health import router as health_router

app = FastAPI(title="GridLens Identity Tenant Service")
app.include_router(health_router)
