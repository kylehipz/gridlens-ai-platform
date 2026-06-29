from fastapi import FastAPI

from gridlens_data_operations_service.api.health import router as health_router

app = FastAPI(title="GridLens Data Operations Service")
app.include_router(health_router)
