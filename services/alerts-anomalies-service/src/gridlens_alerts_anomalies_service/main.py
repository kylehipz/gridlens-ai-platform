from fastapi import FastAPI

from gridlens_alerts_anomalies_service.api.health import router as health_router

app = FastAPI(title="GridLens Alerts Anomalies Service")
app.include_router(health_router)
