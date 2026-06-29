from fastapi import FastAPI

from gridlens_governance_service.api.health import router as health_router

app = FastAPI(title="GridLens Governance Service")
app.include_router(health_router)
