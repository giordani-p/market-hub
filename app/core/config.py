"""Configuracao da aplicacao, lida de variaveis de ambiente."""

from functools import lru_cache
from typing import Literal

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    environment: Literal["local", "staging", "production"] = "local"
    api_prefix: str = "/v1"

    # postgresql+psycopg://<user>:<password>@<host>:<port>/<database>
    database_url: str = ""
    test_database_url: str = ""


@lru_cache
def get_settings() -> Settings:
    return Settings()
