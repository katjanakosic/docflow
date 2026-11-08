"""Application settings, read from environment variables or the repo's .env file."""

from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    database_url: str

    model_config = SettingsConfigDict(env_file="../.env", extra="ignore")

    s3_endpoint_url: str | None = None  # None means Amazon S3
    s3_access_key: str
    s3_secret_key: str
    s3_bucket: str

    redis_url: str

    anthropic_api_key: str
    llm_model: str = "claude-haiku-5-5"


@lru_cache
def get_settings() -> Settings:
    return Settings()
