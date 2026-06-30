from fastapi import FastAPI
from gridlens_observability import instrument_fastapi_app

from gridlens_program_evaluation_service.api.health import router as health_router

app = FastAPI(title="GridLens Program Evaluation Service")
instrument_fastapi_app(app, service_name="program-evaluation-service")
app.include_router(health_router)
