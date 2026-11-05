from pathlib import Path

from fastapi import APIRouter, Response, status
from sqlalchemy import text

from app.core.db import engine

router = APIRouter(prefix="/health", tags=["health"])

# Written by the deploy workflow next to the code, so a deploy can tell when its revision is live.
_BUILD_FILE = Path(__file__).resolve().parents[3] / "BUILD_SHA"
BUILD = _BUILD_FILE.read_text().strip() if _BUILD_FILE.is_file() else "dev"


@router.get("/live", summary="Liveness: the process is up")
async def live() -> dict[str, str]:
    return {"status": "ok", "build": BUILD}


@router.get("/ready", summary="Readiness: the database answers")
async def ready(response: Response) -> dict[str, str]:
    try:
        async with engine.connect() as connection:
            await connection.execute(text("SELECT 1"))
    except Exception:
        response.status_code = status.HTTP_503_SERVICE_UNAVAILABLE
        return {"status": "unavailable"}
    return {"status": "ok"}
