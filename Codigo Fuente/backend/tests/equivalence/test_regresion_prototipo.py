"""Los módulos migrados reproducen exactamente los resultados del prototipo (HU-03).

El archivo de referencia es una copia de
``Prototipo/demand-forecast-hpc/results/baseline_seasonal_naive.csv``, generado por el
prototipo con: 60 series sintéticas, 2023-01-01 a 2026-11-06, semilla 42, sin TRM real,
horizonte 14, 6 orígenes móviles e ingenuo estacional (m = 7).
"""

from pathlib import Path

import numpy as np
import pandas as pd
import pytest

from forecast_core.evaluation.backtesting import rolling_origin_folds
from forecast_core.evaluation.metrics import mape, n_zero_excluded, rmse
from forecast_core.ingestion import synthetic
from forecast_core.models.naive import seasonal_naive
from forecast_core.preprocessing.panel import to_panel


def test_linea_base_identica_al_prototipo(fixtures_dir: Path) -> None:
    esperado = pd.read_csv(fixtures_dir / "prototipo_baseline_seasonal_naive.csv")

    sales, _ = synthetic.generate(n_series=60, start="2023-01-01", end="2026-11-06", seed=42)
    panel = to_panel(sales)
    Y, dates = panel.values, panel.index

    filas = []
    for f in rolling_origin_folds(panel.n_periods, horizon=14, n_folds=6):
        train, test = Y[: f.train_end], Y[f.train_end : f.test_end]
        pred = seasonal_naive(train, 14, season=7)
        filas.append(
            {
                "fold": f.index,
                "train_end": str(dates[f.train_end - 1].date()),
                "RMSE": rmse(test, pred),
                "MAPE_%": mape(test, pred),
                "ceros_excluidos": n_zero_excluded(test),
            }
        )
    obtenido = pd.DataFrame(filas)

    assert panel.n_periods == 1406
    assert panel.n_series == 60
    assert obtenido["train_end"].tolist() == esperado["train_end"].tolist()
    np.testing.assert_allclose(obtenido["RMSE"], esperado["RMSE"], rtol=1e-12)
    np.testing.assert_allclose(obtenido["MAPE_%"], esperado["MAPE_%"], rtol=1e-12)
    assert obtenido["ceros_excluidos"].tolist() == esperado["ceros_excluidos"].tolist()
    assert obtenido["MAPE_%"].mean() == pytest.approx(15.19, abs=0.01)
