"""El IPC sintético está etiquetado y nunca se compara con el informe."""

import pandas as pd

from forecast_core.ingestion import dane_ipc, synthetic
from forecast_core.pipelines.reproduce_oe1 import Check


def test_ipc_sintetico_reproducible_y_etiquetado() -> None:
    a = synthetic.generate_city_cpi(start="2017-01", end="2026-09", seed=1)
    b = synthetic.generate_city_cpi(start="2017-01", end="2026-09", seed=1)
    pd.testing.assert_frame_equal(a, b)
    assert set(a["origin"]) == {"sintetico"}
    assert a.groupby("ciudad").size().to_dict() == {"Cúcuta": 117, "Nacional": 117}


def test_ipc_sintetico_se_lee_como_historia(tmp_path: object) -> None:
    from pathlib import Path

    path = Path(str(tmp_path)) / "ipc.csv"
    synthetic.generate_city_cpi(start="2017-01", end="2017-12").to_csv(path, index=False)
    wide = dane_ipc.load_city_history_csv(path)
    idx = dane_ipc.index_from_monthly_variation(wide["Cúcuta"], base_date="2016-12")
    assert len(idx) == 13
    assert idx.iloc[0] == 100.0


def test_cifras_sinteticas_no_se_comparan() -> None:
    igual = Check("Patrón 3", "Brecha", 0.72, 0.72, 2, sintetico=True)
    assert igual.estado == "sintético (no comparable)"
    assert Check("Patrón 3", "Brecha", 0.72, 0.72, 2).estado == "coincide"
    assert Check("Patrón 3", "Brecha", 0.72, 0.90, 2).estado == "difiere"
    assert Check("Patrón 3", "Brecha", 0.72, None, 2).estado == "pendiente"
