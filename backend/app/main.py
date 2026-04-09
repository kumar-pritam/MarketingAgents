from __future__ import annotations

import os
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.exceptions import RequestValidationError
from starlette.exceptions import HTTPException as StarletteHTTPException

from app.api.router import api_router
from app.core.config import settings
from app.core.logging import configure_logging
from app.core.middleware import setup_middleware
from app.core.handlers import (
    http_exception_handler,
    api_exception_handler,
    validation_exception_handler,
    generic_exception_handler,
    starlette_http_exception_handler,
)
from app.core.exceptions import BaseAPIException

log_file = configure_logging(use_json=os.getenv("LOG_JSON", "false").lower() == "true")

app = FastAPI(
    title=settings.app_name,
    docs_url="/docs" if settings.app_env == "development" else None,
    redoc_url="/redoc" if settings.app_env == "development" else None,
)

setup_middleware(app)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.backend_cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.add_exception_handler(StarletteHTTPException, starlette_http_exception_handler)
app.add_exception_handler(BaseAPIException, api_exception_handler)
app.add_exception_handler(RequestValidationError, validation_exception_handler)
app.add_exception_handler(Exception, generic_exception_handler)

app.include_router(api_router, prefix=settings.api_prefix)


@app.get("/")
def root() -> dict[str, str]:
    return {
        "name": settings.app_name,
        "docs": "/docs",
        "log_file": str(log_file),
    }


@app.get("/health")
def health_check() -> dict[str, str]:
    return {
        "status": "healthy",
        "service": "marketing-agents-backend",
        "version": "1.0.0",
    }
