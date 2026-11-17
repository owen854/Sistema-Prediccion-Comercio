"""Configuración de la API desde variables de entorno (prefijo ``FORECAST_``; RNF-15, RNF-25).

Los secretos nunca se escriben en el código: se leen del entorno o del archivo
``.env`` (que no se versiona; ver ``.env.example``).
"""

from __future__ import annotations

from functools import lru_cache
from typing import Literal

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_prefix="FORECAST_", env_file=".env", env_file_encoding="utf-8", extra="ignore"
    )

    app_name: str = "API del Sistema de Predicción de Demanda"
    environment: Literal["desarrollo", "pruebas", "produccion"] = "desarrollo"
    database_url: str = "postgresql+psycopg://forecast:forecast@localhost:5432/forecast"
    database_connect_timeout_s: int = 3
    cors_origins: list[str] = ["http://localhost:3000"]
    log_level: str = "INFO"


@lru_cache
def get_settings() -> Settings:
    return Settings()
