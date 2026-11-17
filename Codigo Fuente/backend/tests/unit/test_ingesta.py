import pandas as pd

from forecast_core.ingestion import synthetic
from forecast_core.ingestion.trm import parse_trm_rows


def test_sintetico_es_reproducible_y_esta_etiquetado() -> None:
    a, ea = synthetic.generate(n_series=3, start="2024-01-01", end="2024-03-31", seed=7)
    b, _ = synthetic.generate(n_series=3, start="2024-01-01", end="2024-03-31", seed=7)
    pd.testing.assert_frame_equal(a, b)
    assert set(a["origin"]) == {"sintetico"}
    assert set(ea["origin"]) == {"sintetico"}
    assert (a["units"] >= 0).all()
    assert a["series_id"].nunique() == 3


def test_trm_rellena_fines_de_semana_y_no_depende_de_hoy() -> None:
    rows = [
        {"vigenciadesde": "2026-11-06T00:00:00.000", "valor": "4100.5"},  # viernes
        {"vigenciadesde": "2026-11-09T00:00:00.000", "valor": "4120.0"},  # lunes
    ]
    df = parse_trm_rows(rows)
    assert df["date"].dt.strftime("%Y-%m-%d").tolist() == [
        "2026-11-06",
        "2026-11-07",
        "2026-11-08",
        "2026-11-09",
    ]
    assert df["trm_cop_usd"].tolist() == [4100.5, 4100.5, 4100.5, 4120.0]
