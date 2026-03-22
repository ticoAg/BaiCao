from pydantic_settings import BaseSettings, SettingsConfigDict
from functools import lru_cache


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    # App
    app_name: str = "BaiCao ShiTan API"
    debug: bool = False
    api_prefix: str = "/api/v1"

    # Database
    database_url: str = "postgresql+asyncpg://baicao:password@localhost:5432/baicao"
    database_pool_size: int = 10
    database_max_overflow: int = 20

    # Neo4j
    neo4j_uri: str = "bolt://localhost:7687"
    neo4j_user: str = "neo4j"
    neo4j_password: str = "password"

    # LLM
    llm_provider: str = "auto"  # "auto" | "openai" | "anthropic" | "none"
    openai_api_key: str = ""
    openai_model: str = "gpt-4o-mini"
    openai_base_url: str = ""  # 兼容 API（如 DeepSeek、零一万物等）
    anthropic_api_key: str = ""
    anthropic_model: str = "claude-sonnet-4-20250514"
    anthropic_base_url: str = ""  # 兼容 API（如代理中转等）
    llm_temperature: float = 0.7

    # Redis (optional)
    redis_url: str = "redis://localhost:6379"
    redis_enabled: bool = False


@lru_cache
def get_settings() -> Settings:
    return Settings()
