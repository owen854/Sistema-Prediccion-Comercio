"""API de comercios, autorizaciones y conjuntos de datos contra SQLite (HU-09, HU-11)."""

from __future__ import annotations

from collections.abc import Iterator
from pathlib import Path

import pytest
from alembic import command
from alembic.config import Config
from fastapi.testclient import TestClient

from forecast_api.core.config import get_settings
from forecast_api.db.session import get_engine

pytestmark = pytest.mark.integration
BACKEND_DIR = Path(__file__).resolve().parents[2]
CSV = (
    b"fecha,codigo_producto,cantidad,punto_venta,telefono_cliente\n"
    b"2026-01-15,A1,3,Centro,3001234567\n"
    b"2026-01-15,A1,2,Centro,3009876543\n"
    b"2026-01-16,B2,5,Norte,\n"
)


@pytest.fixture
def client(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Iterator[TestClient]:
    url = f"sqlite:///{(tmp_path / 'api.db').as_posix()}"
    monkeypatch.setenv("FORECAST_DATABASE_URL", url)
    monkeypatch.setenv("FORECAST_PSEUDONYM_KEY", "clave-de-prueba")
    get_settings.cache_clear()
    get_engine.cache_clear()
    cfg = Config(str(BACKEND_DIR / "alembic.ini"))
    cfg.set_main_option("sqlalchemy.url", url)
    cfg.attributes["configure_logger"] = False
    command.upgrade(cfg, "head")
    from forecast_api.main import create_app

    yield TestClient(create_app())
    get_settings.cache_clear()
    get_engine.cache_clear()


def _comercio_con_autorizacion(client: TestClient) -> tuple[int, int]:
    com = client.post("/api/v1/comercios", json={"municipio": "Cúcuta", "tipo_negocio": "Tienda"})
    assert com.status_code == 201
    assert com.json()["codigo_seudonimo"].startswith("C")
    cid = com.json()["id"]
    aut = client.post(
        f"/api/v1/comercios/{cid}/autorizaciones",
        json={"fecha": "2026-11-17", "alcance": "Uso de ventas 2025-2026 con fines académicos."},
    )
    assert aut.status_code == 201
    listado = client.get(f"/api/v1/comercios/{cid}/autorizaciones").json()
    assert [a["id"] for a in listado] == [aut.json()["id"]]
    return cid, aut.json()["id"]


def _cargar(client: TestClient, cid: int, aid: int, content: bytes = CSV, name: str = "v.csv"):  # type: ignore[no-untyped-def]
    return client.post(
        "/api/v1/datasets/carga",
        data={"comercio_id": str(cid), "autorizacion_id": str(aid), "nombre": "Ventas 2026"},
        files={"archivo": (name, content, "text/csv")},
    )


def test_carga_anonimiza_versiona_y_reporta_calidad(client: TestClient) -> None:
    cid, aid = _comercio_con_autorizacion(client)
    r = _cargar(client, cid, aid)
    assert r.status_code == 201, r.text
    body = r.json()
    assert body["nueva"] is True
    assert body["version"]["version"] == 1
    assert body["version"]["columnas_eliminadas"] == ["telefono_cliente"]
    assert body["reporte_calidad"]["duplicados"] == 1
    assert body["version"]["filas"] == 2  # A1 del 15 se suma; B2 del 16

    again = _cargar(client, cid, aid)  # mismo archivo: no crea otra versión
    assert again.json()["nueva"] is False

    datasets = client.get("/api/v1/datasets", params={"comercio_id": cid}).json()
    assert len(datasets) == 1
    assert datasets[0]["origen"] == "transaccional"
    did = datasets[0]["id"]
    series = client.get(f"/api/v1/datasets/{did}/versiones/1/series").json()
    assert [(s["clave"], s["observaciones"]) for s in series] == [("A1", 1), ("B2", 1)]
    calidad = client.get(f"/api/v1/datasets/{did}/versiones/1/calidad").json()
    assert calidad["series"] == 2


def test_carga_sin_autorizacion_del_comercio(client: TestClient) -> None:
    cid, _ = _comercio_con_autorizacion(client)
    _, aid_otro = _comercio_con_autorizacion(client)
    r = _cargar(client, cid, aid_otro)
    assert r.status_code == 409
    assert "Ley 1581" in r.json()["detalle"]


def test_carga_invalida_explica_los_problemas(client: TestClient) -> None:
    cid, aid = _comercio_con_autorizacion(client)
    r = _cargar(client, cid, aid, b"fecha,cantidad\n2026-01-01,1\n")
    assert r.status_code == 422
    assert r.json()["problemas"][0]["columna"] == "codigo_producto"


def test_escritura_bloqueada_en_produccion(
    client: TestClient, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setenv("FORECAST_ENVIRONMENT", "produccion")
    get_settings.cache_clear()
    r = client.post("/api/v1/comercios", json={"municipio": "Cúcuta"})
    assert r.status_code == 403


def test_recursos_inexistentes(client: TestClient) -> None:
    assert client.get("/api/v1/datasets/99").status_code == 404
    assert client.get("/api/v1/datasets/99/versiones/1/calidad").status_code == 404
    r = client.post(
        "/api/v1/comercios/99/autorizaciones",
        json={"fecha": "2026-11-17", "alcance": "Uso académico de las ventas."},
    )
    assert r.status_code == 404
