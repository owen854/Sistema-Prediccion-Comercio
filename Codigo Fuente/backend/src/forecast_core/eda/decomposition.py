"""Descomposición clásica multiplicativa y fuerza de la estacionalidad (RF-18; Patrón 2).

Implementación propia (sin statsmodels) según Hyndman y Athanasopoulos (2021), cap. 3:

1. Tendencia-ciclo: media móvil centrada 2×m (para m = 12: pesos 1/24, 1/12, …, 1/12, 1/24).
2. Serie sin tendencia: y / T.
3. Índice estacional de cada mes: promedio de la serie sin tendencia en ese mes,
   normalizado para que los m índices promedien 1.
4. Residuo: y / (T · S).

Fuerza de la estacionalidad: F_S = max(0, 1 − Var(R) / Var(S·R)) sobre la escala
logarítmica, donde la descomposición multiplicativa se vuelve aditiva.
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np
import pandas as pd


@dataclass(frozen=True)
class Decomposition:
    observed: pd.Series
    trend: pd.Series
    seasonal: pd.Series
    resid: pd.Series
    seasonal_index: pd.Series  # índice por periodo del ciclo (1..m), promedio = 1

    @property
    def seasonal_effect_pct(self) -> pd.Series:
        """Efecto estacional en porcentaje (p. ej., diciembre +28,8 %)."""
        return (self.seasonal_index - 1.0) * 100.0


def centered_moving_average(series: pd.Series, period: int) -> pd.Series:
    """Media móvil centrada; para periodo par usa la media 2×m."""
    values = series.to_numpy(dtype=float)
    if period % 2 == 0:
        weights = np.r_[0.5, np.ones(period - 1), 0.5] / period
    else:
        weights = np.ones(period) / period
    half = len(weights) // 2
    trend = np.full(len(values), np.nan)
    if len(values) >= len(weights):
        trend[half : len(values) - half] = np.convolve(values, weights, mode="valid")
    return pd.Series(trend, index=series.index, name="tendencia")


def classical_multiplicative(series: pd.Series, period: int = 12) -> Decomposition:
    """Descomposición clásica multiplicativa de una serie con índice mensual o diario."""
    if (series <= 0).any():
        raise ValueError("La descomposición multiplicativa requiere valores positivos.")
    if len(series) < 2 * period:
        raise ValueError("Se necesitan al menos dos ciclos completos.")
    trend = centered_moving_average(series, period)
    detrended = series / trend
    position = _cycle_position(series.index, period)
    raw_index = detrended.groupby(position).mean()
    seasonal_index = raw_index / raw_index.mean()
    seasonal = pd.Series(
        seasonal_index.reindex(position).to_numpy(), index=series.index, name="estacional"
    )
    resid = (series / (trend * seasonal)).rename("residuo")
    return Decomposition(series, trend, seasonal, resid, seasonal_index.rename("indice"))


def seasonal_strength(dec: Decomposition) -> float:
    """F_S = max(0, 1 − Var(log R) / Var(log S + log R)), sobre los periodos con tendencia."""
    mask = dec.resid.notna()
    log_r = np.log(dec.resid[mask].to_numpy())
    log_s = np.log(dec.seasonal[mask].to_numpy())
    return float(max(0.0, 1.0 - np.var(log_r) / np.var(log_s + log_r)))


def _cycle_position(index: pd.Index, period: int) -> np.ndarray:
    if isinstance(index, pd.DatetimeIndex) and period == 12:
        return np.asarray(index.month)
    if isinstance(index, pd.DatetimeIndex) and period == 7:
        return np.asarray(index.day_of_week)
    return np.arange(len(index)) % period
