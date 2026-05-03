"""
Centralized application configuration using Pydantic Settings.

Loads configuration from environment variables with sensible defaults.
All Google Cloud service configuration is managed here.
"""

import os
from typing import Optional
from pydantic_settings import BaseSettings
from pydantic import Field


class Settings(BaseSettings):
    """
    Application settings loaded from environment variables.

    Attributes:
        app_name: Display name for the application.
        app_version: Semantic version string.
        environment: Deployment environment (development, staging, production).
        log_level: Python logging level.
        gemini_api_key: Google Gemini API key for AI features.
        gemini_model: Gemini model identifier.
        gcp_project_id: Google Cloud project ID for Firestore and Logging.
        firestore_collection: Firestore collection name for analytics data.
        enable_cloud_logging: Whether to use Google Cloud Logging.
        enable_analytics: Whether to track usage analytics in Firestore.
        allowed_origins: Comma-separated CORS origins.
        trusted_hosts: Comma-separated trusted host names.
        rate_limit_global: Global rate limit (requests per minute).
        rate_limit_chat: Chat endpoint rate limit (requests per minute).
    """

    # ── App ─────────────────────────────────────────────────────
    app_name: str = "ElectionGuide AI"
    app_version: str = "1.0.0"
    environment: str = Field(default="production", alias="ENVIRONMENT")
    log_level: str = Field(default="INFO", alias="LOG_LEVEL")

    # ── Google AI ───────────────────────────────────────────────
    gemini_api_key: Optional[str] = Field(default=None, alias="GEMINI_API_KEY")
    gemini_model: str = Field(default="gemini-2.0-flash", alias="GEMINI_MODEL")

    # ── Google Cloud ────────────────────────────────────────────
    gcp_project_id: Optional[str] = Field(default=None, alias="GCP_PROJECT_ID")
    firestore_collection: str = Field(
        default="electionguide_analytics",
        alias="FIRESTORE_COLLECTION",
    )
    enable_cloud_logging: bool = Field(default=True, alias="ENABLE_CLOUD_LOGGING")
    enable_analytics: bool = Field(default=True, alias="ENABLE_ANALYTICS")

    # ── Security ────────────────────────────────────────────────
    allowed_origins: str = Field(default="*", alias="ALLOWED_ORIGINS")
    trusted_hosts: str = Field(default="*", alias="TRUSTED_HOSTS")
    rate_limit_global: str = "60/minute"
    rate_limit_chat: str = "20/minute"

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = False
        extra = "ignore"


# Singleton settings instance
_settings: Optional[Settings] = None


def get_settings() -> Settings:
    """
    Return the cached application settings singleton.

    Returns:
        Settings: The application configuration instance.
    """
    global _settings
    if _settings is None:
        _settings = Settings()
    return _settings
