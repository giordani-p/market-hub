"""Configuracao da aplicacao, lida de variaveis de ambiente."""

from functools import lru_cache
from typing import Literal

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    environment: Literal["local", "staging", "production"] = "local"
    api_prefix: str = "/v1"
    cors_origins: str = "http://localhost:5173,http://localhost:3000"

    # postgresql+psycopg://<user>:<password>@<host>:<port>/<database>
    database_url: str = ""
    test_database_url: str = ""

    jwt_secret: str = ""
    jwt_expire_minutes: int = 60
    seed_password: str = ""
    conversation_inactivity_hours: int = 120

    aws_endpoint_url: str = "http://localhost:4566"
    aws_region: str = "us-east-1"
    jobs_queue_name: str = "market-hub-jobs"
    jobs_dlq_name: str = "market-hub-jobs-dlq"
    jobs_visibility_timeout_seconds: int = 60
    jobs_max_receive_count: int = 3
    jobs_wait_time_seconds: int = 10
    reconcile_page_size: int = 50
    jobs_schedule_expression: str = "rate(15 minutes)"


    @property
    def cors_origins_list(self) -> list[str]:
        return [origin.strip() for origin in self.cors_origins.split(",") if origin.strip()]


@lru_cache
def get_settings() -> Settings:
    return Settings()
