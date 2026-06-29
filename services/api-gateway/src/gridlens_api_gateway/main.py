import uvicorn
from fastapi import FastAPI

from gridlens_api_gateway.api.health import router as health_router
from gridlens_api_gateway.config import load_settings

app = FastAPI(title="GridLens API Gateway Support Service")
app.include_router(health_router)


def main() -> None:
    settings = load_settings()
    uvicorn.run(app, host=settings.host, port=settings.port)


if __name__ == "__main__":
    main()
