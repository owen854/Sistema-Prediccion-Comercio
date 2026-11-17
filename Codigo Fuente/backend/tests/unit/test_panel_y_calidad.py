import numpy as np
import pandas as pd
import pytest

from forecast_core.preprocessing.panel import to_panel
from forecast_core.types import DataOrigin, Panel
from forecast_core.validation.quality import quality_report


@pytest.fixture
def ventas() -> pd.DataFrame:
    # Serie B no tiene registro el 2024-01-02; A tiene un registro duplicado el 2024-01-03.
    return pd.DataFrame(
        {
            "date": [
                "2024-01-01",
                "2024-01-02",
                "2024-01-03",
                "2024-01-03",
                "2024-01-01",
                "2024-01-03",
            ],
            "series_id": ["A", "A", "A", "A", "B", "B"],
            "units": [5, 0, 2, 1, 7, -1],
        }
    )


def test_panel_rellena_con_cero_y_cuenta(ventas: pd.DataFrame) -> None:
    p = to_panel(ventas)
    assert p.series_ids == ("A", "B")
    assert p.values.tolist() == [[5, 7], [0, 0], [3, -1]]  # duplicados de A se suman
    assert p.filled_cells == 1
    assert p.origin is DataOrigin.TRANSACCIONAL


def test_panel_con_nan(ventas: pd.DataFrame) -> None:
    p = to_panel(ventas, fill="nan")
    assert np.isnan(p.values[1, 1])
    assert p.filled_cells == 1


def test_panel_toma_el_origen_de_la_columna(ventas: pd.DataFrame) -> None:
    p = to_panel(ventas.assign(origin="sintetico"))
    assert p.origin is DataOrigin.SINTETICO


def test_panel_rechaza_mezcla_de_origenes(ventas: pd.DataFrame) -> None:
    mezcla = ventas.assign(origin=["sintetico"] * 3 + ["transaccional"] * 3)
    with pytest.raises(ValueError, match="mezcla"):
        to_panel(mezcla)


def test_panel_valida_formas() -> None:
    with pytest.raises(ValueError, match="filas"):
        Panel(
            np.zeros((3, 2)),
            pd.date_range("2024-01-01", periods=2),
            ("a", "b"),
            DataOrigin.PUBLICO,
            "D",
        )


def test_reporte_de_calidad(ventas: pd.DataFrame) -> None:
    r = quality_report(ventas)
    assert r["filas"] == 6
    assert r["series"] == 2
    assert r["periodos_cubiertos"] == 3
    assert r["duplicados"] == 1
    assert r["negativos"] == 1
    assert r["celdas_faltantes"] == 1
    assert r["pct_celdas_faltantes"] == pytest.approx(16.67)
