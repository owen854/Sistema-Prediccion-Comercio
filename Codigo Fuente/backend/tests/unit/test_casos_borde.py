"""Casos borde y de error de los módulos migrados del prototipo."""

import json
import math
from pathlib import Path

import numpy as np
import pytest

from forecast_core.evaluation import metrics as m
from forecast_core.evaluation.backtesting import Fold, check_no_leakage, rolling_origin_folds
from forecast_core.models.naive import (
    MovingAverageForecaster,
    SeasonalNaiveForecaster,
    seasonal_naive,
)
from forecast_core.pipelines import benchmark as pipeline


def test_metricas_sin_denominador_devuelven_nan() -> None:
    assert math.isnan(m.wape([0, 0], [1, 1]))
    assert math.isnan(m.smape([0, 0], [0, 0]))
    assert math.isnan(m.mase([1.0], [1.0], [5.0, 5.0, 5.0]))  # escala 0


def test_mase_exige_historia_mayor_que_la_temporada() -> None:
    with pytest.raises(ValueError, match="periodo estacional"):
        m.mase([1.0], [1.0], [1.0, 2.0], season=7)


def test_parametros_invalidos_de_modelos() -> None:
    with pytest.raises(ValueError, match="al menos 7"):
        seasonal_naive(np.ones((3, 1)), 2, season=7)
    with pytest.raises(ValueError, match="season"):
        SeasonalNaiveForecaster(season=0)
    with pytest.raises(ValueError, match="window"):
        MovingAverageForecaster(window=0)
    with pytest.raises(ValueError, match="al menos 4"):
        MovingAverageForecaster(window=4).fit(np.ones(2))


def test_particiones_invalidas() -> None:
    with pytest.raises(ValueError, match="mayores o iguales a 1"):
        list(rolling_origin_folds(100, horizon=0, n_folds=2))
    with pytest.raises(ValueError, match="retrocede"):
        check_no_leakage([Fold(0, 50, 60), Fold(1, 40, 50)], n_obs=100)


def test_pipeline_benchmark_omp_guarda_resultado(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setenv("FORECAST_PROJECT_ROOT", str(tmp_path))
    args = ["omp", "--series", "4", "--days", "60", "--window", "7", "--repeats", "1"]
    args += ["--threads", "1", "2"]
    assert pipeline.main(args) == 0
    files = list((tmp_path / "experiments" / "results" / "spike").glob("omp_rolling_mean_*.json"))
    assert len(files) == 1
    payload = json.loads(files[0].read_text(encoding="utf-8"))
    assert payload["origen_datos"] == "sintetico"
    assert payload["forma"] == [60, 4]


def test_pipeline_benchmark_mpi_y_resumen(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    monkeypatch.setenv("FORECAST_PROJECT_ROOT", str(tmp_path))
    args = ["mpi", "--series", "3", "--days", "120", "--folds", "4", "--horizon", "7"]
    assert pipeline.main(args) == 0  # sin mpiexec: un proceso, en secuencia
    files = list((tmp_path / "experiments" / "results" / "spike").glob("mpi_backtest_*.json"))
    payload = json.loads(files[0].read_text(encoding="utf-8"))
    assert payload["procesos"] == 1
    assert payload["equivalente_a_secuencial"] is True

    capsys.readouterr()
    assert pipeline.main(["resumen"]) == 0
    resumen = json.loads(capsys.readouterr().out)
    assert resumen["tabla"][0]["aceleracion"] == 1.0
    assert resumen["fraccion_paralelizable_f"] is None  # solo hay T1: no se ajusta Amdahl
