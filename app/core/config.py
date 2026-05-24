"""Application configuration.

Settings are loaded from environment variables (and an optional `.env`
file). Database credentials are kept as separate fields so the same
values can be reused by both the application and the `docker-compose`
PostgreSQL service.
"""

from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Strongly-typed application settings."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    # --- Application -----------------------------------------------------
    app_name: str = "Org Structure API"
    debug: bool = False
    log_level: str = "INFO"

    # --- PostgreSQL ------------------------------------------------------
    postgres_host: str = "db"
    postgres_port: int = 5432
    postgres_user: str = "postgres"
    postgres_password: str = "postgres"
    postgres_db: str = "org_structure"

    @property
    def database_url(self) -> str:
        """Async SQLAlchemy connection URL (asyncpg driver)."""
        return (
            f"postgresql+asyncpg://{self.postgres_user}:{self.postgres_password}"
            f"@{self.postgres_host}:{self.postgres_port}/{self.postgres_db}"
        )


@lru_cache
def get_settings() -> Settings:
    """Return a cached `Settings` instance.

    Cached so the `.env` file and environment are read only once per
    process. Use this as a FastAPI dependency or import `settings` below.
    """
    return Settings()


settings = get_settings()
