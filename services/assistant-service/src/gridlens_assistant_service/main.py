from fastapi import FastAPI
from gridlens_observability import instrument_fastapi_app

from gridlens_assistant_service.api.health import router as health_router

app = FastAPI(title="GridLens Assistant Service")
instrument_fastapi_app(app, service_name="assistant-service")
app.include_router(health_router)
