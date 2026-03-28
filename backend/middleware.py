"""
HTTP middleware:
  - Attaches a unique X-Request-ID to every request (uses incoming header if present)
  - Logs method, path, status, duration for every request
  - Adds X-Request-ID to every response
"""
import time
import uuid
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response
from backend.logger import get_logger

logger = get_logger("api.access")


class RequestLoggingMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next) -> Response:
        request_id = request.headers.get("X-Request-ID") or str(uuid.uuid4())[:8]
        request.state.request_id = request_id

        start = time.perf_counter()
        try:
            response: Response = await call_next(request)
        except Exception:
            elapsed = (time.perf_counter() - start) * 1000
            logger.error(
                "Unhandled exception",
                extra={
                    "request_id": request_id,
                    "method": request.method,
                    "path": request.url.path,
                    "duration_ms": round(elapsed, 1),
                },
                exc_info=True,
            )
            raise

        elapsed = (time.perf_counter() - start) * 1000
        logger.info(
            "%s %s → %s  (%.1fms)",
            request.method,
            request.url.path,
            response.status_code,
            elapsed,
            extra={
                "request_id": request_id,
                "method": request.method,
                "path": request.url.path,
                "status": response.status_code,
                "duration_ms": round(elapsed, 1),
            },
        )
        response.headers["X-Request-ID"] = request_id
        return response
