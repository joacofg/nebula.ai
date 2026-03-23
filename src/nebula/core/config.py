from functools import lru_cache
from typing import Literal

from pydantic import Field, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_name: str = Field(default="Nebula", alias="NEBULA_APP_NAME")
    env: str = Field(default="local", alias="NEBULA_ENV")
    runtime_profile: Literal["local_dev", "premium_first"] = Field(
        default="local_dev",
        alias="NEBULA_RUNTIME_PROFILE",
    )
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
    database_url: str | None = Field(default=None, alias="NEBULA_DATABASE_URL")
    premium_provider: Literal["mock", "openai_compatible"] = Field(
        default="mock",
        alias="NEBULA_PREMIUM_PROVIDER",
    )
    premium_model: str = Field(default="gpt-4o-mini", alias="NEBULA_PREMIUM_MODEL")
    premium_base_url: str | None = Field(default=None, alias="NEBULA_PREMIUM_BASE_URL")
    premium_api_key: str | None = Field(default=None, alias="NEBULA_PREMIUM_API_KEY")
    router_complexity_chars: int = Field(default=400, alias="NEBULA_ROUTER_COMPLEXITY_CHARS")
    enable_metrics: bool = Field(default=True, alias="NEBULA_ENABLE_METRICS")
    data_store_path: str = Field(default=".nebula/nebula.db", alias="NEBULA_DATA_STORE_PATH")
    admin_api_key: str = Field(default="nebula-admin-key", alias="NEBULA_ADMIN_API_KEY")
    bootstrap_tenant_id: str = Field(default="default", alias="NEBULA_BOOTSTRAP_TENANT_ID")
    bootstrap_tenant_name: str = Field(
        default="Default Workspace",
        alias="NEBULA_BOOTSTRAP_TENANT_NAME",
    )
    bootstrap_api_key_name: str = Field(
        default="default-workspace-key",
        alias="NEBULA_BOOTSTRAP_API_KEY_NAME",
    )
    bootstrap_api_key: str = Field(
        default="nebula-dev-key",
        alias="NEBULA_BOOTSTRAP_API_KEY",
    )
    enrollment_token: str | None = Field(default=None, alias="NEBULA_ENROLLMENT_TOKEN")
    hosted_plane_url: str | None = Field(default=None, alias="NEBULA_HOSTED_PLANE_URL")
    remote_management_enabled: bool = Field(
        default=False,
        alias="NEBULA_REMOTE_MANAGEMENT_ENABLED",
    )
    remote_management_allowed_actions: list[str] = Field(
        default_factory=list,
        alias="NEBULA_REMOTE_MANAGEMENT_ALLOWED_ACTIONS",
    )
    remote_management_poll_interval_seconds: int = Field(
        default=60,
        alias="NEBULA_REMOTE_MANAGEMENT_POLL_INTERVAL_SECONDS",
    )

    @model_validator(mode="after")
    def validate_premium_provider_settings(self) -> "Settings":
        if self.env != "local":
            if self.runtime_profile != "premium_first":
                raise ValueError(
                    "NEBULA_RUNTIME_PROFILE must be premium_first when NEBULA_ENV is not local."
                )
            if self.admin_api_key == "nebula-admin-key":
                raise ValueError(
                    "NEBULA_ADMIN_API_KEY must be changed before running outside local mode."
                )
            if self.bootstrap_api_key == "nebula-dev-key":
                raise ValueError(
                    "NEBULA_BOOTSTRAP_API_KEY must be changed before running outside local mode."
                )
            if self.premium_provider == "mock":
                raise ValueError(
                    "NEBULA_PREMIUM_PROVIDER=mock is not allowed when NEBULA_ENV is not local."
                )
            if not self.database_url:
                raise ValueError(
                    "NEBULA_DATABASE_URL must be set when NEBULA_ENV is not local."
                )

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
