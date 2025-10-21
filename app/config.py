import logging
from functools import lru_cache
from typing import List

from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

logger = logging.getLogger(__name__)


class Settings(BaseSettings):
    APP_NAME: str = "Wishlist API"
    ENV: str = "local"
    DEBUG: bool = False

    SECRET_KEY: str = "change-me-in-prod"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30

    DATABASE_URL: str = "postgresql+asyncpg://user:password@localhost:5432/wishlist_db"

    CORS_ORIGINS: List[str] = []

    @field_validator("CORS_ORIGINS", mode="before")
    @classmethod
    def parse_cors(cls, v):
        if not v or isinstance(v, list):
            return v or []
        return [i.strip() for i in v.split(",") if i.strip()]

    @field_validator("SECRET_KEY")
    @classmethod
    def validate_secret_key(cls, v):
        """Validate SECRET_KEY strength on startup."""
        if not v or v == "change-me-in-prod":
            logger.warning("SECRET_KEY is using default value - change in production!")
            return v

        # Import here to avoid circular imports
        from app.services.secrets_service import validate_secret_strength

        is_valid, error = validate_secret_strength(v, "jwt_key")
        if not is_valid:
            logger.error(f"SECRET_KEY validation failed: {error}")
            # Don't raise exception to allow startup, but log the issue
        else:
            logger.info("SECRET_KEY validation passed")

        return v

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
