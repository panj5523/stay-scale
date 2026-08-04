from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_name: str = "Stay Scale API"
    app_version: str = "0.1.0"
    app_env: str = "development"
    app_debug: bool = False
    api_v1_prefix: str = "/api/v1"
    database_url: str = "mysql+aiomysql://stay_scale:stay_scale_dev@127.0.0.1:3307/stay_scale"
    redis_url: str = "redis://127.0.0.1:6379/0"
    cors_origins: str = "http://localhost:5173,http://127.0.0.1:5173"
    ai_provider: str = "local"
    deepseek_api_key: str | None = None
    deepseek_base_url: str = "https://api.deepseek.com"
    deepseek_model: str = "deepseek-v4-flash"
    ai_timeout_seconds: float = 20.0
    auth_secret_key: str = "stay-scale-development-secret-change-me"
    auth_token_expire_minutes: int = 480
    admin_initial_password: str | None = None
    retention_ingestion_days: int = 180
    retention_reviews_days: int = 365
    retention_ai_snapshots_days: int = 180
    retention_recommendation_days: int = 365
    archive_output_dir: str = ".runtime/archives"
    archive_max_records_per_table: int = 10000
    price_freshness_minutes: int = 180
    platform_sync_scheduler_enabled: bool = False
    platform_sync_poll_seconds: int = 60
    platform_sync_retry_attempts: int = 3
    platform_sync_retry_delay_seconds: float = 2.0
    log_format: str = "text"
    log_level: str = "INFO"
    slow_request_threshold_ms: int = 1000

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    @property
    def cors_origin_list(self) -> list[str]:
        return [origin.strip() for origin in self.cors_origins.split(",") if origin.strip()]

    @property
    def deepseek_enabled(self) -> bool:
        return self.ai_provider.lower() == "deepseek" and bool(self.deepseek_api_key)


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
