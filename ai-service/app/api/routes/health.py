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


@router.get("/metrics/dashboard")
async def dashboard_metrics():
    """Get metrics aggregated in JSON format for frontend dashboard visualization."""
    from app.observability.metrics import metrics
    
    vector_search_count = metrics.get_counter("retrieval_search_total", {"method": "vector"})
    bm25_search_count = metrics.get_counter("retrieval_search_total", {"method": "bm25"})
    hybrid_search_count = metrics.get_counter("retrieval_search_total", {"method": "hybrid"})
    
    search_stats_vector = metrics.get_histogram_stats("retrieval_search_duration_ms", {"method": "vector"})
    search_stats_bm25 = metrics.get_histogram_stats("retrieval_search_duration_ms", {"method": "bm25"})
    search_stats_hybrid = metrics.get_histogram_stats("retrieval_search_duration_ms", {"method": "hybrid"})
    
    fusion_stats = metrics.get_histogram_stats("retrieval_fusion_duration_ms")
    rerank_stats = metrics.get_histogram_stats("retrieval_rerank_duration_ms")
    
    gen_count = metrics.get_counter("generation_total")
    gen_stats = metrics.get_histogram_stats("generation_duration_ms")
    token_stats = metrics.get_histogram_stats("generation_tokens_used")
    
    embed_count = metrics.get_counter("embedding_total")
    embed_stats = metrics.get_histogram_stats("embedding_duration_ms")
    
    mem_read_st = metrics.get_counter("memory_read_total", {"memory_type": "short_term"})
    mem_read_lt = metrics.get_counter("memory_read_total", {"memory_type": "long_term"})
    mem_read_ep = metrics.get_counter("memory_read_total", {"memory_type": "episodic"})
    
    mem_write_st = metrics.get_counter("memory_write_total", {"memory_type": "short_term"})
    mem_write_lt = metrics.get_counter("memory_write_total", {"memory_type": "long_term"})
    mem_write_ep = metrics.get_counter("memory_write_total", {"memory_type": "episodic"})
    
    return {
        "retrieval": {
            "search_counts": {
                "vector": vector_search_count,
                "bm25": bm25_search_count,
                "hybrid": hybrid_search_count,
                "total": vector_search_count + bm25_search_count + hybrid_search_count
            },
            "avg_durations": {
                "vector": search_stats_vector["avg"],
                "bm25": search_stats_bm25["avg"],
                "hybrid": search_stats_hybrid["avg"],
                "fusion": fusion_stats["avg"],
                "rerank": rerank_stats["avg"]
            },
            "total_fusions": metrics.get_counter("retrieval_fusion_total"),
            "total_reranks": metrics.get_counter("retrieval_rerank_total")
        },
        "generation": {
            "total_generations": gen_count,
            "avg_duration_ms": gen_stats["avg"],
            "total_tokens": token_stats["sum"],
            "avg_tokens_per_req": token_stats["avg"]
        },
        "embedding": {
            "total_embeddings": embed_count,
            "avg_duration_ms": embed_stats["avg"]
        },
        "memory": {
            "reads": {
                "short_term": mem_read_st,
                "long_term": mem_read_lt,
                "episodic": mem_read_ep,
                "total": mem_read_st + mem_read_lt + mem_read_ep
            },
            "writes": {
                "short_term": mem_write_st,
                "long_term": mem_write_lt,
                "episodic": mem_write_ep,
                "total": mem_write_st + mem_write_lt + mem_write_ep
            }
        }
    }