import os
from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    # App
    app_name: str = "BaiCao ShiTan API"
    debug: bool = False
    api_prefix: str = "/api/v1"
    log_level: str = "INFO"
    log_format: str = "text"  # "text" | "json"

    # Database
    database_url: str = "postgresql+asyncpg://baicao:password@localhost:5432/baicao"
    database_pool_size: int = 10
    database_max_overflow: int = 20

    # Neo4j
    neo4j_uri: str = "bolt://localhost:7687"
    neo4j_user: str = "neo4j"
    neo4j_password: str = "password"

    # LLM（仅 OpenAI 兼容接口，例如 Fireworks）
    llm_provider: str = "openai"  # "openai" | "none"
    openai_api_key: str = ""
    openai_model: str = "gpt-4o-mini"
    openai_base_url: str = ""
    llm_temperature: float = 0.7

    # 问答循环中的结构化判定。留空则不注册 judge。
    typesafe_api_key: str = ""
    typesafe_base_url: str = ""
    typesafe_model: str = "decision-model-preview"
    typesafe_timeout_seconds: float = 60

    # Redis (optional)
    redis_url: str = "redis://localhost:6379"
    redis_enabled: bool = False

    # Object Storage
    object_storage_endpoint: str = "localhost:19000"
    object_storage_access_key: str = "minioadmin"
    object_storage_secret_key: str = "minioadmin"
    object_storage_bucket: str = "baicao-pipeline-exports"
    object_storage_secure: bool = False

    # Pipeline Source Storage
    pipeline_source_storage_dir: str = "tmp/data"


@lru_cache
def get_settings() -> Settings:
    if not os.environ.get("INFISICAL_SECRETS_LOADED"):
        from .infisical_secrets import apply_to_process_env

        apply_to_process_env()
    return Settings()
