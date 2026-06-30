from fastapi import FastAPI
from gridlens_observability import instrument_fastapi_app

from gridlens_alerts_anomalies_service.api.health import router as health_router

app = FastAPI(title="GridLens Alerts Anomalies Service")
instrument_fastapi_app(app, service_name="alerts-anomalies-service")
app.include_router(health_router)
