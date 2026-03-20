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
    openai_api_key: str = ""
    openai_model: str = "gpt-4o-mini"
    llm_temperature: float = 0.7

    # Redis (optional)
    redis_url: str = "redis://localhost:6379"
    redis_enabled: bool = False


@lru_cache
def get_settings() -> Settings:
    return Settings()
