from __future__ import annotations

from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict

_HERE = Path(__file__).resolve()
_BACKEND_ENV = _HERE.parents[2] / ".env"
_ROOT_ENV = _HERE.parents[3] / ".env"


class Settings(BaseSettings):
    app_name: str = "Marketing Agents Platform"
    app_env: str = "development"
    api_prefix: str = "/api/v1"
    openrouter_api_key: str | None = None
    openrouter_base_url: str = "https://openrouter.ai/api/v1"
    openrouter_model: str = "meta-llama/llama-3.3-70b-instruct:free"
    openrouter_ssl_verify: bool = True
    openrouter_ca_bundle: str | None = None
    openrouter_dev_insecure_fallback: bool = True
    backend_cors_origins: list[str] = [
        "http://localhost:3000",
        "http://127.0.0.1:3000",
    ]
    max_upload_mb: int = 25

    # Database
    database_url: str = "postgresql://postgres:@localhost:5432/kumarpritam"
    use_database: bool = True

    model_config = SettingsConfigDict(
        env_file=(str(_BACKEND_ENV), str(_ROOT_ENV), ".env"),
        env_file_encoding="utf-8",
        extra="ignore",
    )


settings = Settings()
