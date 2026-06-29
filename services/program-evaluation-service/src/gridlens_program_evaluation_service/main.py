from fastapi import FastAPI

from gridlens_program_evaluation_service.api.health import router as health_router

app = FastAPI(title="GridLens Program Evaluation Service")
app.include_router(health_router)
