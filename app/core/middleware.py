import time
import uuid
from typing import Callable
from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware
import structlog
from contextvars import ContextVar

# Context variables for logging and tracing
request_id_var: ContextVar[str] = ContextVar("request_id", default="")
correlation_id_var: ContextVar[str] = ContextVar("correlation_id", default="")

class RequestIDMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        # Check for incoming Correlation-ID or generate one
        correlation_id = request.headers.get("X-Correlation-ID", str(uuid.uuid4()))
        req_id = str(uuid.uuid4())
        
        request_id_var.set(req_id)
        correlation_id_var.set(correlation_id)
        
        # Bind context variables to structured logger for this request
        structlog.contextvars.bind_contextvars(
            request_id=req_id,
            correlation_id=correlation_id,
            client_ip=request.client.host if request.client else None
        )
        
        start_time = time.perf_counter()
        
        try:
            response = await call_next(request)
        except Exception as exc:
            # Bind exception info to logger
            structlog.get_logger().exception("Unhandled exception processing request", exc_info=exc)
            raise
        finally:
            process_time = time.perf_counter() - start_time
            # Clear contextvars to prevent memory leaks in async tasks
            structlog.contextvars.clear_contextvars()
            
        response.headers["X-Request-ID"] = req_id
        response.headers["X-Correlation-ID"] = correlation_id
        response.headers["X-Process-Time"] = str(process_time)
        return response
