"""API y migraciones contra SQLite (no requiere PostgreSQL)."""

from __future__ import annotations

from collections.abc import Iterator
from pathlib import Path

import pytest
from alembic import command
from alembic.autogenerate import compare_metadata
from alembic.config import Config
from alembic.migration import MigrationContext
from fastapi.testclient import TestClient
from sqlalchemy import create_engine

from forecast_api.core.config import get_settings
from forecast_api.db import models  # noqa: F401
from forecast_api.db.base import Base
from forecast_api.db.session import get_engine

pytestmark = pytest.mark.integration
BACKEND_DIR = Path(__file__).resolve().parents[2]


@pytest.fixture
def db_url(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Iterator[str]:
    url = f"sqlite:///{(tmp_path / 'prueba.db').as_posix()}"
    monkeypatch.setenv("FORECAST_DATABASE_URL", url)
    get_settings.cache_clear()
    get_engine.cache_clear()
    yield url
    get_settings.cache_clear()
    get_engine.cache_clear()


def _alembic_config(url: str) -> Config:
    cfg = Config(str(BACKEND_DIR / "alembic.ini"))
    cfg.set_main_option("sqlalchemy.url", url)
    cfg.attributes["configure_logger"] = False
    return cfg


def test_migraciones_coinciden_con_los_modelos(db_url: str) -> None:
    command.upgrade(_alembic_config(db_url), "head")
    engine = create_engine(db_url)
    with engine.connect() as conn:
        diferencias = compare_metadata(MigrationContext.configure(conn), Base.metadata)
    assert diferencias == [], f"Los modelos y las migraciones difieren: {diferencias}"
    command.downgrade(_alembic_config(db_url), "base")


def test_health_con_base_de_datos(db_url: str) -> None:
    from forecast_api.main import create_app

    r = TestClient(create_app()).get("/health")
    assert r.status_code == 200
    body = r.json()
    assert body["status"] == "ok"
    assert body["base_de_datos"] == "ok"
    assert set(body["capacidades"]) == {"openmp_kernels", "mpi4py", "cuda"}


def test_health_sin_base_de_datos(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv(
        "FORECAST_DATABASE_URL", "postgresql+psycopg://nadie:nada@127.0.0.1:1/inexistente"
    )
    monkeypatch.setenv("FORECAST_DATABASE_CONNECT_TIMEOUT_S", "1")
    get_settings.cache_clear()
    get_engine.cache_clear()
    from forecast_api.main import create_app

    try:
        r = TestClient(create_app()).get("/health")
        assert r.status_code == 200
        assert r.json()["status"] == "degradado"
        assert r.json()["base_de_datos"] == "no_disponible"
    finally:
        get_settings.cache_clear()
        get_engine.cache_clear()


def test_openapi_disponible(db_url: str) -> None:
    from forecast_api.main import create_app

    spec = TestClient(create_app()).get("/openapi.json").json()
    assert "/health" in spec["paths"]
