"""Health check route."""

from fastapi import APIRouter, Depends
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from api.deps import get_db

router = APIRouter(prefix="/health", tags=["health"])


@router.get("")
async def health_check():
    """Liveness probe — always returns OK if the process is running."""
    return {"status": "ok"}


@router.get("/db")
async def db_health(db: AsyncSession = Depends(get_db)):
    """Readiness probe — checks database connectivity."""
    await db.execute(text("SELECT 1"))
    return {"status": "ok", "database": "connected"}
