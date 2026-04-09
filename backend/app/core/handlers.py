from __future__ import annotations

import logging
import traceback
from datetime import datetime, timezone
from typing import Optional
from fastapi import Request, HTTPException
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from starlette.exceptions import HTTPException as StarletteHTTPException

logger = logging.getLogger(__name__)


def get_request_id(request: Request) -> str:
    return getattr(request.state, "request_id", "unknown")


def format_error_response(
    message: str,
    request_id: str,
    error_code: Optional[str] = None,
    details: Optional[dict] = None,
    status_code: int = 500,
) -> dict:
    return {
        "error": True,
        "message": message,
        "request_id": request_id,
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "status_code": status_code,
        "error_code": error_code,
        "details": details,
    }


async def http_exception_handler(request: Request, exc: HTTPException) -> JSONResponse:
    request_id = get_request_id(request)
    
    if isinstance(exc.detail, dict):
        error_data = exc.detail
    else:
        error_data = {
            "error": True,
            "message": str(exc.detail),
            "request_id": request_id,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "status_code": exc.status_code,
        }
    
    logger.warning(
        f"HTTP {exc.status_code} | {request.method} {request.url.path} | Request ID: {request_id}"
    )
    
    return JSONResponse(status_code=exc.status_code, content=error_data)


async def api_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    request_id = get_request_id(request)
    
    if hasattr(exc, "detail") and isinstance(exc.detail, dict):
        error_data = exc.detail
        error_data["request_id"] = request_id
        error_data["timestamp"] = datetime.now(timezone.utc).isoformat()
        status_code = getattr(exc, "status_code", 500)
    else:
        error_data = format_error_response(
            message=str(exc),
            request_id=request_id,
            error_code=exc.__class__.__name__,
        )
        status_code = 500
    
    logger.error(
        f"API Exception | {exc.__class__.__name__} | {request.method} {request.url.path} | Request ID: {request_id}",
        exc_info=True,
    )
    
    return JSONResponse(status_code=status_code, content=error_data)


async def validation_exception_handler(request: Request, exc: RequestValidationError) -> JSONResponse:
    request_id = get_request_id(request)
    
    errors = []
    for error in exc.errors():
        errors.append({
            "field": ".".join(str(loc) for loc in error["loc"]),
            "message": error["msg"],
            "type": error["type"],
        })
    
    error_data = format_error_response(
        message="Validation error",
        request_id=request_id,
        error_code="VALIDATION_ERROR",
        details={"errors": errors},
        status_code=422,
    )
    
    logger.warning(
        f"Validation Error | {request.method} {request.url.path} | Request ID: {request_id}",
        extra={"errors": errors},
    )
    
    return JSONResponse(status_code=422, content=error_data)


async def generic_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    request_id = get_request_id(request)
    
    error_trace = traceback.format_exc()
    
    logger.critical(
        f"Unhandled Exception | {exc.__class__.__name__} | {request.method} {request.url.path} | Request ID: {request_id}",
        exc_info=True,
    )
    
    error_data = format_error_response(
        message="An unexpected error occurred",
        request_id=request_id,
        error_code="INTERNAL_ERROR",
        status_code=500,
    )
    
    return JSONResponse(status_code=500, content=error_data)


async def starlette_http_exception_handler(request: Request, exc: StarletteHTTPException) -> JSONResponse:
    request_id = get_request_id(request)
    
    error_data = format_error_response(
        message=exc.detail,
        request_id=request_id,
        error_code="HTTP_ERROR",
        status_code=exc.status_code,
    )
    
    logger.warning(
        f"HTTP {exc.status_code} | {request.method} {request.url.path} | Request ID: {request_id}"
    )
    
    return JSONResponse(status_code=exc.status_code, content=error_data)
