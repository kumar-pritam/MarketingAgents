from __future__ import annotations

from fastapi import APIRouter

from app.api.routes import agents, health, integrations, workspace
from app.api.routes.admin import router as admin_router
from app.api.routes.auth import router as auth_router

api_router = APIRouter()
api_router.include_router(health.router)
api_router.include_router(workspace.router)
api_router.include_router(integrations.router)
api_router.include_router(agents.router)
api_router.include_router(auth_router)
api_router.include_router(admin_router)
