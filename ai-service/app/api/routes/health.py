"""
MemoraAI - API Routes: Health
Health check and status endpoints.
"""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional
import structlog

from db.connection import db

logger = structlog.get_logger(__name__)
router = APIRouter(prefix="/health", tags=["health"])


class HealthResponse(BaseModel):
    status: str
    version: str
    database: str
    timestamp: str


@router.get("/", response_model=HealthResponse)
async def health_check():
    """Basic health check endpoint."""
    try:
        await db.execute("SELECT 1")
        db_status = "connected"
    except Exception:
        db_status = "disconnected"

    return HealthResponse(
        status="healthy" if db_status == "connected" else "degraded",
        version="1.0.0",
        database=db_status,
        timestamp="",
    )


@router.get("/ready")
async def readiness_check():
    """Readiness check for deployment."""
    try:
        await db.execute("SELECT 1")
        return {"ready": True, "checks": {"database": "ok"}}
    except Exception as e:
        logger.error("readiness_check_failed", error=str(e))
        raise HTTPException(status_code=503, detail="Service not ready")


@router.get("/live")
async def liveness_check():
    """Liveness check for container orchestration."""
    return {"alive": True}