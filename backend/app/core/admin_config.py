from pydantic_settings import BaseSettings
from functools import lru_cache


class AdminSettings(BaseSettings):
    admin_password_hash: str = "pbkdf2_sha256$383200$placeholder"  # Default placeholder
    admin_username: str = "admin"
    use_real_password: bool = False

    class Config:
        env_file = ".env"
        env_prefix = "ADMIN_"


@lru_cache()
def get_admin_settings() -> AdminSettings:
    return AdminSettings()
