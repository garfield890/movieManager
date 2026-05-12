from fastapi import APIRouter, Depends
from src.api import auth

router = APIRouter(
    prefix="/health",
    tags=["health"],
    dependencies=[Depends(auth.get_api_key)],
)

@router.get("/", tags=["meta"])
def read_health() -> dict[str, str]:
    return {"status": "healthy"}