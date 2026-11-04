from fastapi import APIRouter, Response, status
from sqlalchemy import text

from app.core.db import engine

router = APIRouter(prefix="/health", tags=["health"])


@router.get("/live", summary="Liveness: the process is up")
async def live() -> dict[str, str]:
    return {"status": "ok"}


@router.get("/ready", summary="Readiness: the database answers")
async def ready(response: Response) -> dict[str, str]:
    try:
        async with engine.connect() as connection:
            await connection.execute(text("SELECT 1"))
    except Exception:
        response.status_code = status.HTTP_503_SERVICE_UNAVAILABLE
        return {"status": "unavailable"}
    return {"status": "ok"}
