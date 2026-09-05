from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    app_name: str = "llmllm"
    app_env: str = "dev"
    app_host: str = "0.0.0.0"
    app_port: int = 8000
    postgres_dsn: str = "postgresql+asyncpg://llmllm:llmllm@localhost:5432/llmllm"
    qdrant_url: str = "http://localhost:6333"
    qdrant_api_key: str | None = None
    llm_provider: str | None = None
    llm_model: str | None = None
    llm_api_key: str | None = None
    llm_base_url: str | None = None
    embedding_model: str | None = None
    retrieval_backend: str = "hybrid"  # hybrid (Qdrant dense + local sparse) | local
    rerank: bool = True
    intent_classify: bool = True


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
