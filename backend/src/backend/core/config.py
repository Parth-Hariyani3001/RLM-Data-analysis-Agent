from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_name: str = "RLM Data Agent"
    environment: str = "development"
    debug: bool = True

    database_url: str = ""
    redis_url: str = "redis://localhost:6379/0"

    model_provider: str = "openai"
    model_name: str = ""

    llm_base_url: str = "http://localhost:1234/v1"
    llm_api_key: str = "lm-studio"
    llm_model: str = "google/gemma-4-e4b"

    storage_path: str = "storage"
    max_upload_size_mb: int = 500

    jwt_secret_key: str = ""
    jwt_algorithm: str = "HS256"
    jwt_expire_minutes: int = 60

    cors_origins: list[str] = ["http://localhost:5173"]

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
