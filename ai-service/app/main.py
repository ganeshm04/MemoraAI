"""
MemoraAI - FastAPI Application
Main entry point for the AI microservice.
Trigger reload for schema update v3.
"""

from contextlib import asynccontextmanager
from fastapi import FastAPI, Request, Response
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import structlog

from app.config import config
from app.api.routes import health, ingest, query, search, memory
from db.connection import db
from app.observability.middleware import ObservabilityMiddleware
from app.observability.metrics import metrics

logger = structlog.get_logger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan management."""
    logger.info("application_starting", version=config.settings.APP_VERSION)

    try:
        await db.connect()
        logger.info("database_connected")
    except Exception as e:
        logger.warning("database_connection_skipped", error=str(e))

    yield

    logger.info("application_shutting_down")
    await db.disconnect()


app = FastAPI(
    title=config.settings.APP_NAME,
    version=config.settings.APP_VERSION,
    description="MemoraAI - Adaptive RAG System with Hybrid Retrieval and Memory",
    lifespan=lifespan,
)


app.add_middleware(
    CORSMiddleware,
    allow_origins=[origin.strip() for origin in config.settings.CORS_ORIGINS.split(",") if origin.strip()],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
app.add_middleware(ObservabilityMiddleware)


@app.get("/metrics")
async def prometheus_metrics():
    """Prometheus metrics scrape endpoint."""
    return Response(content=metrics.to_prometheus_format(), media_type="text/plain")


@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    """Global exception handler."""
    logger.error(
        "unhandled_exception",
        path=request.url.path,
        error=str(exc),
        error_type=type(exc).__name__,
    )
    return JSONResponse(
        status_code=500,
        content={
            "error": "Internal server error",
            "detail": str(exc) if config.settings.DEBUG else "An error occurred",
        },
    )


app.include_router(health.router, prefix="/api/v1")
app.include_router(ingest.router, prefix="/api/v1")
app.include_router(query.router, prefix="/api/v1")
app.include_router(search.router, prefix="/api/v1")
app.include_router(memory.router, prefix="/api/v1")


@app.get("/")
async def root():
    """Root endpoint."""
    return {
        "name": config.settings.APP_NAME,
        "version": config.settings.APP_VERSION,
        "status": "running",
    }


@app.get("/api/v1")
async def api_info():
    """API information endpoint."""
    return {
        "version": "1.0.0",
        "endpoints": {
            "health": "/api/v1/health",
            "ingest": "/api/v1/ingest/{pdf,url,text}",
            "query": "/api/v1/query",
            "search": "/api/v1/search/{vector,bm25,hybrid}",
            "memory": "/api/v1/memory/{short,long,episodic}",
        },
    }


if __name__ == "__main__":
    import uvicorn
    
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8000,
        reload=config.settings.DEBUG,
        log_level=config.settings.LOG_LEVEL.lower(),
    )