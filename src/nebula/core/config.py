from functools import lru_cache
from typing import Literal

from pydantic import Field, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_name: str = Field(default="Nebula", alias="NEBULA_APP_NAME")
    env: str = Field(default="local", alias="NEBULA_ENV")
    api_v1_prefix: str = Field(default="/v1", alias="NEBULA_API_V1_PREFIX")
    default_model: str = Field(default="nebula-auto", alias="NEBULA_DEFAULT_MODEL")
    log_level: str = Field(default="INFO", alias="NEBULA_LOG_LEVEL")
    ollama_base_url: str = Field(default="http://localhost:11434", alias="NEBULA_OLLAMA_BASE_URL")
    local_model: str = Field(default="llama3.2:3b", alias="NEBULA_LOCAL_MODEL")
    embedding_model: str = Field(default="nomic-embed-text", alias="NEBULA_EMBEDDING_MODEL")
    embedding_dimensions: int = Field(default=768, alias="NEBULA_EMBEDDING_DIMENSIONS")
    qdrant_url: str = Field(default="http://localhost:6333", alias="NEBULA_QDRANT_URL")
    semantic_cache_collection: str = Field(
        default="nebula-semantic-cache",
        alias="NEBULA_SEMANTIC_CACHE_COLLECTION",
    )
    semantic_cache_threshold: float = Field(
        default=0.90,
        alias="NEBULA_SEMANTIC_CACHE_THRESHOLD",
    )
    premium_provider: Literal["mock", "openai_compatible"] = Field(
        default="mock",
        alias="NEBULA_PREMIUM_PROVIDER",
    )
    premium_model: str = Field(default="gpt-4o-mini", alias="NEBULA_PREMIUM_MODEL")
    premium_base_url: str | None = Field(default=None, alias="NEBULA_PREMIUM_BASE_URL")
    premium_api_key: str | None = Field(default=None, alias="NEBULA_PREMIUM_API_KEY")
    router_complexity_chars: int = Field(default=400, alias="NEBULA_ROUTER_COMPLEXITY_CHARS")
    enable_metrics: bool = Field(default=True, alias="NEBULA_ENABLE_METRICS")

    @model_validator(mode="after")
    def validate_premium_provider_settings(self) -> "Settings":
        if self.premium_provider != "openai_compatible":
            return self

        if not self.premium_base_url or not self.premium_base_url.strip():
            raise ValueError(
                "NEBULA_PREMIUM_BASE_URL is required when "
                "NEBULA_PREMIUM_PROVIDER=openai_compatible."
            )
        if not self.premium_api_key or not self.premium_api_key.strip():
            raise ValueError(
                "NEBULA_PREMIUM_API_KEY is required when "
                "NEBULA_PREMIUM_PROVIDER=openai_compatible."
            )
        if not self.premium_model.strip():
            raise ValueError(
                "NEBULA_PREMIUM_MODEL is required when "
                "NEBULA_PREMIUM_PROVIDER=openai_compatible."
            )
        return self

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
        populate_by_name=True,
    )


@lru_cache
def get_settings() -> Settings:
    return Settings()
