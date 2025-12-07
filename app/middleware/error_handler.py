"""
Global Exception Handler Middleware

Provides:
- Request ID tracking for distributed tracing
- Structured error logging with context
- Response time monitoring
- Consistent error response format
- Production-ready error handling
"""
from fastapi import Request
from fastapi.responses import JSONResponse
from app.logging_config import get_logger
import traceback
import time
import uuid

logger = get_logger(__name__)


async def error_handler_middleware(request: Request, call_next):
    """
    Global error handling middleware.
    
    Features:
    - Adds unique request_id to every request
    - Logs all requests with timing
    - Catches and logs exceptions
    - Returns structured error responses
    
    Args:
        request: FastAPI Request
        call_next: Next middleware/handler
    
    Returns:
        Response or JSONResponse (on error)
    """
    # Generate unique request ID for tracing
    request_id = str(uuid.uuid4())
    request.state.request_id = request_id
    
    start_time = time.time()
    
    try:
        response = await call_next(request)
        duration_ms = (time.time() - start_time) * 1000
        
        # Log successful request
        logger.info(
            f"Request completed: {request.method} {request.url.path}",
            extra={
                "request_id": request_id,
                "method": request.method,
                "path": request.url.path,
                "status_code": response.status_code,
                "duration_ms": round(duration_ms, 2)
            }
        )
        
        # Add request ID to response headers
        response.headers["X-Request-ID"] = request_id
        
        return response
        
    except Exception as exc:
        duration_ms = (time.time() - start_time) * 1000
        
        # Log error with full context
        logger.error(
            f"Request failed: {type(exc).__name__} - {str(exc)}",
            extra={
                "request_id": request_id,
                "method": request.method,
                "path": request.url.path,
                "error_type": type(exc).__name__,
                "error_message": str(exc),
                "duration_ms": round(duration_ms, 2)
            },
            exc_info=True  # Include full traceback
        )
        
        # Return structured error response
        return JSONResponse(
            status_code=500,
            content={
                "error": type(exc).__name__,
                "detail": str(exc),
                "request_id": request_id,
                "path": request.url.path
            },
            headers={"X-Request-ID": request_id}
        )
