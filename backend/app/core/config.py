import os
from typing import Optional
from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    APP_NAME: str = "HITRAG Backend"
    ENV: str = "development"
    DEBUG: bool = True
    PORT: int = 8000
    DATABASE_URL: str = "postgresql://user:password@localhost:5432/hitrag"

    # JWT Authentication Security Settings
    SECRET_KEY: str = "b271c8216463e1f056695d4db121f2b0eb979284d1f44aa834bc521fbbae9b80"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24  # 24 Hours

    # Gemini API Settings (Phase 11 — Embeddings)
    GEMINI_API_KEY: Optional[str] = None

    # CORS Allowed Origins
    ALLOWED_ORIGINS: list[str] = [
        "http://localhost:3000",
        "http://127.0.0.1:3000",
    ]

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore"
    )

def get_settings() -> Settings:
    return Settings()

settings = get_settings()
