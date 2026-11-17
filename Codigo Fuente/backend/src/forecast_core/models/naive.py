"""Modelos de referencia (RF-24): ingenuo, ingenuo estacional y media móvil.

Son la "vara mínima": cualquier modelo complejo (SARIMA, Prophet, LSTM) debe
superarlos; si no, su costo no se justifica (Tabla 2 del documento y RNF-01).

``seasonal_naive`` se migró de ``baselines.py`` del prototipo; ahora el periodo
estacional es configurable según la frecuencia (7 diaria, 52 semanal, 12 mensual).
"""

from __future__ import annotations

from typing import Self

import numpy as np

from forecast_core.models.base import Forecast, Forecaster, as_2d

SEASON_BY_FREQ = {"D": 7, "W": 52, "MS": 12, "M": 12}


def seasonal_naive(train: np.ndarray, horizon: int, season: int = 7) -> np.ndarray:
    """Repite la última temporada observada. ``train``: ``(T, N)``; devuelve ``(horizon, N)``."""
    if train.shape[0] < season:
        raise ValueError(f"Se necesitan al menos {season} periodos; hay {train.shape[0]}.")
    last_season = train[-season:]
    reps = int(np.ceil(horizon / season))
    return np.tile(last_season, (reps, 1))[:horizon]


class NaiveForecaster(Forecaster):
    """Pronostica el último valor observado."""

    name = "ingenuo"

    def fit(self, y: np.ndarray, X: np.ndarray | None = None) -> Self:
        self._last = as_2d(y)[-1:].copy()
        return self

    def predict(self, horizon: int, X_future: np.ndarray | None = None) -> Forecast:
        return Forecast(mean=np.repeat(self._last, horizon, axis=0))


class SeasonalNaiveForecaster(Forecaster):
    """Pronostica que cada periodo será igual al mismo periodo de la temporada anterior."""

    name = "ingenuo_estacional"

    def __init__(self, season: int = 7) -> None:
        if season < 1:
            raise ValueError("season debe ser mayor o igual a 1.")
        self.season = season

    def fit(self, y: np.ndarray, X: np.ndarray | None = None) -> Self:
        y2 = as_2d(y)
        if y2.shape[0] < self.season:
            raise ValueError(f"Se necesitan al menos {self.season} periodos.")
        self._train_tail = y2[-self.season :].copy()
        return self

    def predict(self, horizon: int, X_future: np.ndarray | None = None) -> Forecast:
        return Forecast(mean=seasonal_naive(self._train_tail, horizon, self.season))


class MovingAverageForecaster(Forecaster):
    """Pronostica el promedio de los últimos ``window`` periodos."""

    name = "media_movil"

    def __init__(self, window: int = 4) -> None:
        if window < 1:
            raise ValueError("window debe ser mayor o igual a 1.")
        self.window = window

    def fit(self, y: np.ndarray, X: np.ndarray | None = None) -> Self:
        y2 = as_2d(y)
        if y2.shape[0] < self.window:
            raise ValueError(f"Se necesitan al menos {self.window} periodos.")
        self._level = y2[-self.window :].mean(axis=0, keepdims=True)
        return self

    def predict(self, horizon: int, X_future: np.ndarray | None = None) -> Forecast:
        return Forecast(mean=np.repeat(self._level, horizon, axis=0))
