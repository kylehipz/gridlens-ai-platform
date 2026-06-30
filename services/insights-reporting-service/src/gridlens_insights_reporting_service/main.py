from fastapi import FastAPI
from gridlens_observability import instrument_fastapi_app

from gridlens_insights_reporting_service.api.health import router as health_router

app = FastAPI(title="GridLens Insights Reporting Service")
instrument_fastapi_app(app, service_name="insights-reporting-service")
app.include_router(health_router)
