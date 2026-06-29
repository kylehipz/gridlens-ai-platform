from fastapi import FastAPI

from gridlens_insights_reporting_service.api.health import router as health_router

app = FastAPI(title="GridLens Insights Reporting Service")
app.include_router(health_router)
