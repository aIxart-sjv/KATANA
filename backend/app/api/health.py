from fastapi import APIRouter

router = APIRouter(prefix="/api")


@router.get("/health")
async def health():
    return {
        "status": "healthy",
        "service": "KATANA Backend",
        "version": "0.1.0",
    }