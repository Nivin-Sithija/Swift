from functools import lru_cache
from pathlib import Path

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_prefix="SWIFT_", extra="ignore")

    environment: str = "development"
    database_url: str = "postgresql+asyncpg://swift:swift@postgres:5432/swift"
    redis_url: str = "redis://redis:6379/0"
    secret_key: str = Field(
        default="development-only-change-me-at-least-32-characters", min_length=32
    )
    access_token_minutes: int = 15
    refresh_token_days: int = 7
    cors_origins: str = "http://localhost:5173,http://localhost:8080"
    storage_root: Path = Path("storage")
    max_upload_bytes: int = 10 * 1024 * 1024
    low_confidence_threshold: float = 0.60
    use_inline_processing: bool = True
    agent_registration_code: str | None = None
    groq_api_key: str | None = None
    groq_model: str = "llama-3.3-70b-versatile"
    gemini_api_key: str | None = None
    gemini_model: str = "gemini-2.5-flash"
    rag_embedding_model: str = "BAAI/bge-m3"
    rag_embedding_provider: str = "local"
    huggingface_token: str | None = None
    intent_model_id: str = "Swift-Support/labse-intent-1.0"
    intent_space_url: str = "https://ruththra-labse-intent-demo.hf.space"
    intent_request_timeout_seconds: float = 60.0
    huggingface_provider: str = "hf-inference"
    huggingface_endpoint_url: str | None = None
    rag_embedding_dimensions: int = 1024
    rag_candidate_limit: int = 20
    rag_final_limit: int = 5
    rag_min_confidence: float = 0.55
    rag_review_max_age_days: int = 365
    rag_request_timeout_seconds: float = 20.0

    @field_validator("database_url")
    @classmethod
    def normalize_async_database_url(cls, value: str) -> str:
        """Accept standard Postgres URLs while always using SQLAlchemy's asyncpg driver."""
        if value.startswith("postgres://"):
            return value.replace("postgres://", "postgresql+asyncpg://", 1)
        if value.startswith("postgresql://"):
            return value.replace("postgresql://", "postgresql+asyncpg://", 1)
        return value

    @property
    def allowed_origins(self) -> list[str]:
        return [origin.strip() for origin in self.cors_origins.split(",") if origin.strip()]


@lru_cache
def get_settings() -> Settings:
    return Settings()
