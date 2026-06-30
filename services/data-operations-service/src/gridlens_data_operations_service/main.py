from fastapi import FastAPI
from gridlens_observability import instrument_fastapi_app

from gridlens_data_operations_service.api.health import router as health_router

app = FastAPI(title="GridLens Data Operations Service")
instrument_fastapi_app(app, service_name="data-operations-service")
app.include_router(health_router)
