from fastapi import APIRouter

router = APIRouter(tags=["health"])


@router.get("/health")
@router.get("/healthz")
def read_health() -> dict[str, str]:
    return {"status": "ok", "service": "identity-tenant-service"}
