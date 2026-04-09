from __future__ import annotations

import os
from dataclasses import dataclass

from dotenv import load_dotenv

load_dotenv()


@dataclass(frozen=True)
class Settings:
    openrouter_api_key: str | None = os.getenv("OPENROUTER_API_KEY")
    openrouter_base_url: str = os.getenv("OPENROUTER_BASE_URL", "https://openrouter.ai/api/v1")
    openrouter_model: str = os.getenv(
        "OPENROUTER_MODEL", "meta-llama/llama-3.3-70b-instruct:free"
    )
    openrouter_fallback_model: str = os.getenv("OPENROUTER_FALLBACK_MODEL", "openrouter/free")
    max_retries: int = int(os.getenv("MAX_RETRIES", "3"))
    quota_warn_threshold: int = int(os.getenv("QUOTA_WARN_THRESHOLD", "150"))
    quota_daily_limit: int = int(os.getenv("QUOTA_DAILY_LIMIT", "200"))


settings = Settings()
