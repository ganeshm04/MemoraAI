"""
MemoraAI - API Routes: Health
Health check and status endpoints.
"""

from datetime import datetime
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional
import structlog

from db.connection import db
from app.config import config

logger = structlog.get_logger(__name__)
router = APIRouter(prefix="/health", tags=["health"])


class HealthResponse(BaseModel):
    status: str
    version: str
    database: str
    timestamp: str
    environment: str = "development"


class DetailedHealthResponse(BaseModel):
    status: str
    version: str
    database: str
    gemini_api: str
    embedding_model: str
    reranker_model: str
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
        version=config.settings.APP_VERSION,
        database=db_status,
        timestamp=datetime.utcnow().isoformat(),
        environment=config.settings.ENVIRONMENT,
    )


@router.get("/ready")
async def readiness_check():
    """Readiness check for deployment."""
    checks = {}

    # Database check
    try:
        await db.execute("SELECT 1")
        checks["database"] = "ok"
    except Exception as e:
        checks["database"] = f"error: {str(e)[:50]}"

    # Gemini API key check
    checks["gemini_api_key"] = "configured" if config.settings.GEMINI_API_KEY else "missing"

    all_ok = checks.get("database") == "ok" and checks.get("gemini_api_key") == "configured"

    if not all_ok:
        raise HTTPException(
            status_code=503,
            detail={"ready": False, "checks": checks},
        )

    return {"ready": True, "checks": checks}


@router.get("/live")
async def liveness_check():
    """Liveness check for container orchestration."""
    return {"alive": True, "timestamp": datetime.utcnow().isoformat()}


@router.get("/detailed", response_model=DetailedHealthResponse)
async def detailed_health():
    """Detailed health check with all dependencies."""
    try:
        await db.execute("SELECT 1")
        db_status = "connected"
    except Exception:
        db_status = "disconnected"

    return DetailedHealthResponse(
        status="healthy" if db_status == "connected" else "degraded",
        version=config.settings.APP_VERSION,
        database=db_status,
        gemini_api="configured" if config.settings.GEMINI_API_KEY else "missing",
        embedding_model=config.settings.EMBEDDING_MODEL,
        reranker_model=config.settings.RERANKER_MODEL,
        timestamp=datetime.utcnow().isoformat(),
    )


@router.get("/metrics")
async def health_metrics():
    """Expose metrics in Prometheus format."""
    from fastapi import Response
    from app.observability.metrics import metrics
    return Response(content=metrics.to_prometheus_format(), media_type="text/plain")