from decimal import Decimal
from fastapi import FastAPI
from src.api.movies import router as movies_router
from src.api.users import router as users_router
from src.api.health import router as health_router
from starlette.middleware.cors import CORSMiddleware

app = FastAPI(
    title="Movie Manager API",
    summary="Backend API for tracking users and their saved movies.",
    version="0.1.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_credentials=True,
    allow_methods=["GET", "OPTIONS", "POST", "PUT"],
    allow_headers=["*"],
)

app.include_router(movies_router)
app.include_router(users_router)
app.include_router(health_router)

@app.get("/", tags=["meta"])
def read_root() -> dict[str, str]:
    return {
        "service": "movieManager",
        "status": "ok",
        "docs": "/docs",
    }