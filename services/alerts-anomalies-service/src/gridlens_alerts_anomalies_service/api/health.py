from fastapi import APIRouter

router = APIRouter(tags=["health"])


@router.get("/health")
@router.get("/healthz")
async def read_health() -> dict[str, str]:
    return {"status": "ok", "service": "alerts-anomalies-service"}
