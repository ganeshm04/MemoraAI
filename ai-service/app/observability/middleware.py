import time
import uuid
from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware
import structlog
from app.observability.logger import add_context, clear_context
from app.observability.metrics import metrics

logger = structlog.get_logger(__name__)


class ObservabilityMiddleware(BaseHTTPMiddleware):
    """
    Middleware for end-to-end request tracing, logging, and metrics collection.
    
    Acts as the entry point for FastAPI requests:
    - Extracts or generates correlation IDs (x-request-id)
    - Integrates correlation ID to structlog contexts
    - Captures request count and route latency metrics
    """

    async def dispatch(self, request: Request, call_next):
        # 1. Extract request ID from incoming request headers or generate a UUID
        request_id = request.headers.get("x-request-id") or str(uuid.uuid4())
        
        # 2. Inject context parameters
        clear_context()
        add_context("request_id", request_id)
        
        # Also map standard request labels if present
        session_id = request.headers.get("x-session-id")
        if session_id:
            add_context("session_id", session_id)
            
        user_id = request.headers.get("x-user-id")
        if user_id:
            add_context("user_id", user_id)

        start_time = time.perf_counter()
        
        # Default placeholder response in case of downstream failures
        response = Response("Internal Server Error", status_code=500)
        
        try:
            # Increment request counter metric
            metrics.increment(
                "http_requests_total",
                labels={
                    "method": request.method,
                    "endpoint": request.url.path,
                }
            )
            
            logger.info("request_started", method=request.method, path=request.url.path)
            
            # 3. Call downstream handlers
            response = await call_next(request)
            
            duration_ms = (time.perf_counter() - start_time) * 1000.0
            
            # Record execution latency
            metrics.timing(
                "http_request",
                duration_ms,
                labels={
                    "method": request.method,
                    "endpoint": request.url.path,
                    "status": str(response.status_code),
                }
            )
            
            logger.info(
                "request_completed",
                method=request.method,
                path=request.url.path,
                status_code=response.status_code,
                duration_ms=round(duration_ms, 2),
            )
            
        except Exception as exc:
            duration_ms = (time.perf_counter() - start_time) * 1000.0
            metrics.increment(
                "http_request_errors_total",
                labels={
                    "method": request.method,
                    "endpoint": request.url.path,
                    "error_type": type(exc).__name__,
                }
            )
            logger.error(
                "request_failed",
                method=request.method,
                path=request.url.path,
                error=str(exc),
                duration_ms=round(duration_ms, 2),
                exc_info=True,
            )
            raise exc
            
        finally:
            # Bind request trace header to response
            response.headers["x-request-id"] = request_id
            clear_context()
            
        return response
