"""Centralized configuration using pydantic-settings."""

from __future__ import annotations

from pathlib import Path
from typing import Literal

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    # Application
    app_name: str = "iPerson"
    app_version: str = "0.1.0"
    debug: bool = False
    environment: Literal["development", "staging", "production"] = "development"
    log_level: str = "INFO"

    # Database
    database_url: str = "postgresql+asyncpg://iperson:iperson@localhost:5432/iperson"
    database_url_sync: str = "postgresql://iperson:iperson@localhost:5432/iperson"

    # Redis
    redis_url: str = "redis://localhost:6379/0"

    # JWT
    jwt_secret_key: str = "change-me-in-production"
    jwt_algorithm: str = "HS256"
    jwt_access_token_expire_minutes: int = 30
    jwt_refresh_token_expire_days: int = 7

    # LLM API Keys
    openai_api_key: str = ""
    anthropic_api_key: str = ""

    # Celery
    celery_broker_url: str = "redis://localhost:6379/1"
    celery_result_backend: str = "redis://localhost:6379/2"

    # Storage
    s3_endpoint: str = "http://localhost:9000"
    s3_access_key: str = "minioadmin"
    s3_secret_key: str = "minioadmin"
    s3_bucket: str = "iperson-media"

    # CORS
    cors_origins: list[str] = ["http://localhost:3000"]

    # Pipeline
    pipeline_quality_threshold: float = 0.7
    pipeline_dedup_window_hours: int = 48
    pipeline_similarity_threshold: float = 0.85

    @property
    def base_dir(self) -> Path:
        return Path(__file__).resolve().parent.parent.parent


settings = Settings()