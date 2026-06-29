from fastapi import FastAPI

from gridlens_assistant_service.api.health import router as health_router

app = FastAPI(title="GridLens Assistant Service")
app.include_router(health_router)
