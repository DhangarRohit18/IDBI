"""
FinTwin AI — Application Configuration
All settings loaded from environment variables via Pydantic BaseSettings.
Never hardcode secrets.
"""

from __future__ import annotations

import json
from functools import lru_cache
from typing import Any

from pydantic import AnyHttpUrl, EmailStr, Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # ---- Application ----
    APP_NAME: str = "FinTwin AI"
    APP_VERSION: str = "1.0.0"
    APP_ENV: str = Field(default="development", pattern="^(development|staging|production)$")
    DEBUG: bool = False
    SECRET_KEY: str = Field(min_length=32)
    ALLOWED_HOSTS: list[str] = ["localhost", "127.0.0.1"]
    CORS_ORIGINS: list[str] = ["http://localhost:3000"]

    @field_validator("CORS_ORIGINS", "ALLOWED_HOSTS", mode="before")
    @classmethod
    def parse_list(cls, v: Any) -> list[str]:
        if isinstance(v, str):
            try:
                return json.loads(v)
            except json.JSONDecodeError:
                return [item.strip() for item in v.split(",")]
        return v

    # ---- Database ----
    DATABASE_URL: str = Field(
        default="postgresql+asyncpg://fintwin_app:password@localhost:5432/fintwin_db"
    )
    DATABASE_POOL_SIZE: int = 20
    DATABASE_MAX_OVERFLOW: int = 10
    DATABASE_POOL_TIMEOUT: int = 30
    DATABASE_POOL_RECYCLE: int = 3600

    # ---- Redis ----
    REDIS_URL: str = "redis://localhost:6379/0"
    REDIS_CACHE_DB: int = 1
    REDIS_SESSION_DB: int = 2
    REDIS_DEFAULT_TTL: int = 300  # 5 minutes

    # ---- Qdrant ----
    QDRANT_HOST: str = "localhost"
    QDRANT_PORT: int = 6333
    QDRANT_API_KEY: str = ""
    QDRANT_TWIN_COLLECTION: str = "msme_twins"
    QDRANT_EVAL_COLLECTION: str = "evaluation_reports"

    # ---- JWT ----
    SECRET_KEY: str = Field(min_length=32)
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 15
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7

    # ---- Celery ----
    CELERY_BROKER_URL: str = "redis://localhost:6379/3"
    CELERY_RESULT_BACKEND: str = "redis://localhost:6379/4"
    CELERY_TASK_SERIALIZER: str = "json"
    CELERY_RESULT_SERIALIZER: str = "json"
    CELERY_ACCEPT_CONTENT: list[str] = ["json"]
    CELERY_TIMEZONE: str = "Asia/Kolkata"

    # ---- AI / LLM ----
    GEMINI_API_KEY: str = ""
    GEMINI_MODEL: str = "gemini-1.5-pro"
    LLM_TIMEOUT_SECONDS: int = 60
    LLM_MAX_RETRIES: int = 3

    # ---- External APIs ----
    GSTN_BASE_URL: str = "https://api.gstn.gov.in/v2"
    GSTN_API_KEY: str = ""
    CREDIT_BUREAU_URL: str = "https://api.cibil.com/v1"
    CREDIT_BUREAU_KEY: str = ""
    MARKET_DATA_URL: str = "https://api.marketdata.app/v1"
    MARKET_DATA_KEY: str = ""

    # ---- Email (SendGrid) ----
    SENDGRID_API_KEY: str = ""
    SENDGRID_FROM_EMAIL: str = "noreply@fintwin.ai"
    SENDGRID_FROM_NAME: str = "FinTwin AI"

    # ---- SMS (Twilio) ----
    TWILIO_ACCOUNT_SID: str = ""
    TWILIO_AUTH_TOKEN: str = ""
    TWILIO_FROM_NUMBER: str = ""

    # ---- File Storage ----
    STORAGE_BACKEND: str = "local"  # local | s3
    LOCAL_STORAGE_PATH: str = "./storage/uploads"
    MAX_UPLOAD_SIZE_MB: int = 50

    # ---- Rate Limiting ----
    RATE_LIMIT_PER_USER_PER_MIN: int = 100
    RATE_LIMIT_AI_PER_USER_PER_MIN: int = 10
    RATE_LIMIT_AUTH_PER_MIN: int = 10

    # ---- Encryption ----
    ENCRYPTION_KEY: str = Field(min_length=32)

    # ---- Logging ----
    LOG_LEVEL: str = "INFO"
    SENTRY_DSN: str = ""

    # ---- EWS Configuration ----
    EWS_GST_NONFILE_WARNING_MONTHS: int = 2
    EWS_GST_NONFILE_CRITICAL_MONTHS: int = 3
    EWS_REVENUE_DECLINE_WARNING_PCT: float = 20.0
    EWS_REVENUE_DECLINE_CRITICAL_PCT: float = 40.0
    EWS_CREDIT_DROP_WARNING_POINTS: int = 50
    EWS_CREDIT_DROP_CRITICAL_POINTS: int = 100

    # ---- Risk Configuration ----
    RISK_PD_SENIOR_REVIEW_THRESHOLD: float = 0.40
    RISK_FRAUD_AUTO_REJECT_THRESHOLD: float = 0.90
    RISK_MAX_OFFICER_APPROVAL_AMOUNT: float = 5_000_000.0

    # ---- Digital Twin ----
    DIGITAL_TWIN_EXPIRY_DAYS: int = 30
    DIGITAL_TWIN_EMBEDDING_MODEL: str = "intfloat/e5-small-v2"
    DIGITAL_TWIN_EMBEDDING_DIM: int = 384

    @property
    def is_production(self) -> bool:
        return self.APP_ENV == "production"

    @property
    def is_development(self) -> bool:
        return self.APP_ENV == "development"

    @property
    def max_upload_bytes(self) -> int:
        return self.MAX_UPLOAD_SIZE_MB * 1024 * 1024


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    """Return cached settings instance. Avoids re-reading .env on every call."""
    return Settings()


# Module-level convenience import
settings: Settings = get_settings()
