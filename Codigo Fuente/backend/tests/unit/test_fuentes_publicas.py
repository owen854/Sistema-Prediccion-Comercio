"""Lectores de fuentes públicas con archivos de prueba que imitan la estructura oficial."""

import json
from pathlib import Path

import numpy as np
import openpyxl
import pandas as pd
import pytest

from forecast_core.ingestion import common, dane_emc, dane_ipc, migracion, trm


def _emc_xlsx(path: Path) -> Path:
    wb = openpyxl.Workbook()
    ws = wb.active
    ws.title = "1.2"
    ws.append([None, "Encuesta Mensual de Comercio"])
    ws.append([None, "1.2 Índices empalmados de las ventas en valores reales"])
    ws.append([])
    ws.append([None, "Año", "Mes", "Total comercio minorista sin otros vehículos", "Otra"])
    for i, mes in enumerate(["  Noviembre", "Diciembre"]):
        ws.append([None, 2013 if i == 0 else None, mes, 70.0 + i, 1.0])
    ws.append([None, 2014, "Enero", 80.0, 1.0])
    ws.append([None, None, "Febrero", 81.0, 1.0])
    ws.append([None, "Fuente: DANE - EMC"])
    wb.save(path)
    return path


def test_lector_emc(tmp_path: Path) -> None:
    s = dane_emc.parse_emc_index(_emc_xlsx(tmp_path / "emc.xlsx"))
    assert s.index.strftime("%Y-%m").tolist() == ["2013-11", "2013-12", "2014-01", "2014-02"]
    assert s.tolist() == [70.0, 71.0, 80.0, 81.0]


def test_lector_emc_columna_inexistente(tmp_path: Path) -> None:
    with pytest.raises(ValueError, match="no tiene la columna"):
        dane_emc.parse_emc_index(_emc_xlsx(tmp_path / "emc.xlsx"), column="No existe")


def test_lector_ipc_ciudades(tmp_path: Path) -> None:
    wb = openpyxl.Workbook()
    ws = wb.active
    ws.title = "4"
    ws.append(["IPC. Variación mensual"])
    ws.append(["Septiembre de 2026"])
    ws.append(["Ciudades", "Alimentos", "Total"])
    ws.append(["Total IPC", 0.78, 0.37])
    ws.append(["Cúcuta", 0.94, 0.5])
    ws.append([])
    ws.append(["Fuente: DANE."])
    wb.save(tmp_path / "ipc.xlsx")
    s = dane_ipc.parse_city_monthly_variation(tmp_path / "ipc.xlsx")
    assert s.attrs["fecha"] == pd.Timestamp("2026-09-01")
    assert s.to_dict() == {"Total IPC": 0.37, "Cúcuta": 0.5}


def test_indice_desde_variaciones() -> None:
    v = pd.Series([1.0, 2.0], index=pd.to_datetime(["2017-01-01", "2017-02-01"]))
    idx = dane_ipc.index_from_monthly_variation(v, base_date="2016-12")
    np.testing.assert_allclose(idx.to_numpy(), [100.0, 101.0, 103.02])
    with pytest.raises(ValueError, match="después del mes base"):
        dane_ipc.index_from_monthly_variation(v, base_date="2017-01")


def test_historia_ipc_csv(tmp_path: Path) -> None:
    (tmp_path / "ipc.csv").write_text(
        "fecha,ciudad,variacion_pct\n2017-01-15,Cúcuta,1.1\n2017-01-15,Nacional,1.0\n",
        encoding="utf-8",
    )
    wide = dane_ipc.load_city_history_csv(tmp_path / "ipc.csv")
    assert wide.index[0] == pd.Timestamp("2017-01-01")
    assert wide.loc["2017-01-01", "Cúcuta"] == 1.1


PUESTOS = {"(1,1)": "A", "(2,2)": "B"}


def test_migracion_suma_puestos_y_aplica_regla_de_faltantes() -> None:
    rows = [
        {"a_o": "2020", "mes": "Marzo", "ubicacion_pcm": "(1,1)", "total": "10"},
        {"a_o": "2020", "mes": "Marzo", "ubicacion_pcm": "(2,2)", "total": "5"},
        {"a_o": "2020", "mes": "Mayo", "ubicacion_pcm": "(1,1)", "total": "3"},
        {"a_o": "2020", "mes": "Mayo", "ubicacion_pcm": "(9,9)", "total": "999"},  # otro puesto
    ]
    df = migracion.parse_migracion(rows, PUESTOS)
    total, rellenados = migracion.monthly_entries(df, {"2020-04": 0})
    assert total.tolist() == [15.0, 0.0, 3.0]
    assert rellenados == ["2020-04"]
    with pytest.raises(ValueError, match="sin regla de relleno"):
        migracion.monthly_entries(df)


def test_consulta_soql_filtra_puestos() -> None:
    params = migracion.soql_params(["(1,1)", "(2,2)"])
    assert params["$where"] == "ubicacion_pcm in('(1,1)','(2,2)')"
    assert "sum(total)" in params["$select"]


def test_trm_desde_json(tmp_path: Path) -> None:
    rows = [{"vigenciadesde": "2026-11-06T00:00:00.000", "valor": "4100"}]
    (tmp_path / "trm.json").write_text(json.dumps(rows), encoding="utf-8")
    assert trm.load_trm_json(tmp_path / "trm.json")["trm_cop_usd"].tolist() == [4100.0]


def test_meses_en_espanol() -> None:
    assert common.parse_spanish_month("  Septiembre") == 9
    assert (
        common.parse_spanish_month("Agosto p") is None or common.parse_spanish_month("Agostop") == 8
    )
    assert common.parse_spanish_month("Total") is None


def test_manifiesto_registra_hash(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("FORECAST_PROJECT_ROOT", str(tmp_path))
    f = tmp_path / "data" / "raw" / "public" / "x.csv"
    f.parent.mkdir(parents=True)
    f.write_text("a,b\n1,2\n", encoding="utf-8")
    common.register_in_manifest(f, fuente="prueba")
    entry = common.register_in_manifest(f, fuente="prueba", url="https://ejemplo")
    manifest = json.loads((tmp_path / "data" / "manifest.json").read_text(encoding="utf-8"))
    assert len(manifest["archivos"]) == 1  # se reemplaza, no se duplica
    assert entry["archivo"] == "data/raw/public/x.csv"
    assert entry["sha256"] == common.sha256_file(f)


def test_descarga_solo_https() -> None:
    with pytest.raises(ValueError, match="HTTPS"):
        common.download("http://inseguro.example", "data/raw/x.bin")
