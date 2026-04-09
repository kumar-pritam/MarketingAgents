from __future__ import annotations

import time
from datetime import datetime, timezone

from fastapi import APIRouter

router = APIRouter(tags=["health"])


@router.get("/health")
async def health_check():
    return {
        "status": "healthy",
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "service": "marketing-agents-backend",
        "version": "1.0.0",
    }


@router.get("/ping")
async def ping():
    return {"pong": True, "time": int(time.time())}
