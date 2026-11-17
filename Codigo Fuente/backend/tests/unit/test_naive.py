from pathlib import Path

import numpy as np
import pytest

from forecast_core.models.naive import (
    MovingAverageForecaster,
    NaiveForecaster,
    SeasonalNaiveForecaster,
    seasonal_naive,
)


def test_ingenuo_estacional_repite_la_ultima_temporada() -> None:
    train = np.arange(1, 15, dtype=float)[:, None]  # 14 días
    pred = seasonal_naive(train, horizon=10, season=7)
    assert pred[:, 0].tolist() == [8, 9, 10, 11, 12, 13, 14, 8, 9, 10]


def test_clase_y_funcion_coinciden(rng: np.random.Generator) -> None:
    y = rng.poisson(20, size=(60, 5)).astype(float)
    fc = SeasonalNaiveForecaster(season=7).fit(y).predict(14)
    np.testing.assert_array_equal(fc.mean, seasonal_naive(y, 14, 7))
    assert fc.horizon == 14


def test_ingenuo_y_media_movil() -> None:
    y = np.array([1.0, 2.0, 3.0, 4.0])
    assert NaiveForecaster().fit(y).predict(3).mean[:, 0].tolist() == [4, 4, 4]
    assert MovingAverageForecaster(window=2).fit(y).predict(2).mean[:, 0].tolist() == [3.5, 3.5]


def test_historia_insuficiente_falla() -> None:
    with pytest.raises(ValueError, match="al menos 7"):
        SeasonalNaiveForecaster(season=7).fit(np.ones(3))


def test_guardar_y_cargar(tmp_path: Path) -> None:
    y = np.arange(30, dtype=float)
    model = SeasonalNaiveForecaster(season=7).fit(y)
    path = tmp_path / "modelo.pkl"
    model.save(path)
    loaded = SeasonalNaiveForecaster.load(path)
    np.testing.assert_array_equal(loaded.predict(7).mean, model.predict(7).mean)
