"""
Global exception handlers.

Converts all errors to a consistent JSON envelope:
  {"error": "<type>", "detail": "<message>", "request_id": "<id>"}

Handlers:
  - RequestValidationError  → 422 with field-level details
  - HTTPException           → pass-through with envelope
  - Exception               → 500, hides internals in prod
"""
from fastapi import FastAPI, Request, HTTPException
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from backend.logger import get_logger

logger = get_logger("api.errors")


def _request_id(request: Request) -> str:
    return getattr(request.state, "request_id", "-")


def register_exception_handlers(app: FastAPI) -> None:

    @app.exception_handler(RequestValidationError)
    async def validation_error_handler(request: Request, exc: RequestValidationError):
        errors = [
            {"field": ".".join(str(loc) for loc in e["loc"]), "msg": e["msg"]}
            for e in exc.errors()
        ]
        logger.warning(
            "Validation error %s %s — %s",
            request.method, request.url.path, errors,
            extra={"request_id": _request_id(request)},
        )
        return JSONResponse(
            status_code=422,
            content={
                "error": "validation_error",
                "detail": errors,
                "request_id": _request_id(request),
            },
        )

    @app.exception_handler(HTTPException)
    async def http_exception_handler(request: Request, exc: HTTPException):
        level = logger.warning if exc.status_code < 500 else logger.error
        level(
            "HTTP %s — %s %s",
            exc.status_code, request.method, request.url.path,
            extra={
                "request_id": _request_id(request),
                "detail": exc.detail,
            },
        )
        return JSONResponse(
            status_code=exc.status_code,
            content={
                "error": "http_error",
                "detail": exc.detail,
                "request_id": _request_id(request),
            },
            headers=dict(exc.headers or {}),
        )

    @app.exception_handler(Exception)
    async def unhandled_exception_handler(request: Request, exc: Exception):
        logger.exception(
            "Unhandled exception %s %s",
            request.method, request.url.path,
            extra={"request_id": _request_id(request)},
        )
        return JSONResponse(
            status_code=500,
            content={
                "error": "internal_server_error",
                "detail": "An unexpected error occurred.",
                "request_id": _request_id(request),
            },
        )
