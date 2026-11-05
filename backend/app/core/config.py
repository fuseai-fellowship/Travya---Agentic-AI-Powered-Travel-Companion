"""Application settings, read once from the environment (12-factor)."""

from functools import lru_cache
from typing import Literal, Self

from pydantic import Field, SecretStr, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

Environment = Literal["local", "test", "staging", "production"]


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_ignore_empty=True, extra="ignore")

    ENVIRONMENT: Environment = "local"
    PROJECT_NAME: str = "Travya"
    API_V1_PREFIX: str = "/api/v1"
    FRONTEND_ORIGINS: list[str] = ["http://localhost:5173"]
    LOG_LEVEL: str = "INFO"
    LOG_JSON: bool = False
    SENTRY_DSN: str | None = None
    ENABLE_CLOUD_TRACE: bool = False  # export ADK agent/LLM spans to Cloud Trace

    # Postgres 17 with pgvector. Neon needs `?sslmode=require` in the URL.
    DATABASE_URL: str = "postgresql+psycopg://travya:travya@localhost:5433/travya"
    DB_POOL_SIZE: int = 5
    # Redis (Upstash in production: rediss://...). Without it, limits and cache stay in memory.
    REDIS_URL: str | None = None

    # Firebase Authentication. Locally the Auth emulator is used via FIREBASE_AUTH_EMULATOR_HOST.
    FIREBASE_PROJECT_ID: str = "demo-travya"

    # Gemini (Google AI Studio free tier)
    GEMINI_API_KEY: SecretStr | None = None
    GEMINI_MODEL: str = "gemini-flash-latest"
    GEMINI_FALLBACK_MODEL: str = "gemini-flash-lite-latest"
    GEMINI_EMBEDDING_MODEL: str = "gemini-embedding-001"  # batches; -2 merges inputs
    EMBEDDING_DIM: int = 768
    LLM_DAILY_REQUEST_BUDGET: int = Field(
        default=400, description="Global cap on agent runs per day"
    )

    # Abuse controls (per user)
    RATE_LIMIT_DEFAULT: str = "120/minute"
    RATE_LIMIT_PLAN: str = "6/hour"
    RATE_LIMIT_CHAT: str = "40/hour"

    # External services. OFFLINE_INTEGRATIONS swaps every adapter for its fake (tests, demos without network).
    OFFLINE_INTEGRATIONS: bool = False
    HTTP_USER_AGENT: str = "Travya/1.0 (+https://github.com/fuseai-fellowship/Travya---Agentic-AI-Powered-Travel-Companion)"
    HTTP_TIMEOUT_SECONDS: float = 15.0
    UNSPLASH_ACCESS_KEY: SecretStr | None = None
    ORS_API_KEY: SecretStr | None = None

    # File storage for trip documents
    STORAGE_BACKEND: Literal["local", "gcs", "database"] = "local"
    LOCAL_STORAGE_DIR: str = "./.storage"
    GCS_BUCKET: str | None = None
    MAX_UPLOAD_MB: int = 10

    @property
    def is_production(self) -> bool:
        return self.ENVIRONMENT in ("staging", "production")

    @model_validator(mode="after")
    def _require_production_secrets(self) -> Self:
        if not self.is_production:
            return self
        missing = [
            name
            for name, value in (
                ("GEMINI_API_KEY", self.GEMINI_API_KEY),
                ("REDIS_URL", self.REDIS_URL),
                ("GCS_BUCKET", self.GCS_BUCKET if self.STORAGE_BACKEND == "gcs" else "n/a"),
            )
            if not value
        ]
        if "localhost" in self.DATABASE_URL:
            missing.append("DATABASE_URL")
        if missing:
            raise ValueError(f"Missing production settings: {', '.join(missing)}")
        return self


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
