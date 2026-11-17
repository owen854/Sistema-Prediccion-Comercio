"""Métricas de error de pronóstico (RF-41; Hyndman y Koehler, 2006).

RMSE = sqrt( (1/n) Σ (y − ŷ)² )
MAE  = (1/n) Σ |y − ŷ|
MAPE = (100/n) Σ |(y − ŷ) / y|          (solo puntos con y ≠ 0)
WAPE = 100 · Σ |y − ŷ| / Σ |y|
sMAPE = (100/n) Σ 2|y − ŷ| / (|y| + |ŷ|) (solo puntos con |y| + |ŷ| > 0)
MASE = MAE / MAE del ingenuo estacional dentro del entrenamiento

Aviso metodológico: el MAPE no está definido cuando y = 0, algo común en ventas
diarias por producto. Aquí esos puntos se excluyen y :func:`n_zero_excluded`
informa cuántos fueron, para no esconder el problema. Para series con muchos
ceros se recomienda WAPE o MASE (revisión sistemática del proyecto).
"""

from __future__ import annotations

import numpy as np
from numpy.typing import ArrayLike


def _pair(y_true: ArrayLike, y_pred: ArrayLike) -> tuple[np.ndarray, np.ndarray]:
    a = np.asarray(y_true, dtype=float)
    b = np.asarray(y_pred, dtype=float)
    if a.shape != b.shape:
        raise ValueError(f"Formas distintas: y_true {a.shape} vs y_pred {b.shape}.")
    return a, b


def rmse(y_true: ArrayLike, y_pred: ArrayLike) -> float:
    a, b = _pair(y_true, y_pred)
    return float(np.sqrt(np.mean((a - b) ** 2)))


def mae(y_true: ArrayLike, y_pred: ArrayLike) -> float:
    a, b = _pair(y_true, y_pred)
    return float(np.mean(np.abs(a - b)))


def mape(y_true: ArrayLike, y_pred: ArrayLike) -> float:
    """MAPE en porcentaje, excluyendo los puntos con valor real igual a 0."""
    a, b = _pair(y_true, y_pred)
    mask = a != 0
    if not mask.any():
        return float("nan")
    return float(100.0 * np.mean(np.abs((a[mask] - b[mask]) / a[mask])))


def n_zero_excluded(y_true: ArrayLike) -> int:
    """Cantidad de puntos excluidos del MAPE por tener valor real 0."""
    return int(np.sum(np.asarray(y_true) == 0))


def wape(y_true: ArrayLike, y_pred: ArrayLike) -> float:
    """Error porcentual absoluto ponderado; estable con ceros."""
    a, b = _pair(y_true, y_pred)
    denom = np.sum(np.abs(a))
    if denom == 0:
        return float("nan")
    return float(100.0 * np.sum(np.abs(a - b)) / denom)


def smape(y_true: ArrayLike, y_pred: ArrayLike) -> float:
    """MAPE simétrico en porcentaje (0 a 200)."""
    a, b = _pair(y_true, y_pred)
    denom = np.abs(a) + np.abs(b)
    mask = denom > 0
    if not mask.any():
        return float("nan")
    return float(100.0 * np.mean(2.0 * np.abs(a[mask] - b[mask]) / denom[mask]))


def mase(y_true: ArrayLike, y_pred: ArrayLike, y_train: ArrayLike, season: int = 1) -> float:
    """Error absoluto escalado por el ingenuo estacional del entrenamiento.

    Para matrices ``(T, N)`` la escala se calcula por serie (columna) y se promedia
    el error escalado de todas las series. Un valor < 1 significa que el modelo es
    mejor que el ingenuo estacional dentro de la muestra.
    """
    a, b = _pair(y_true, y_pred)
    train = np.asarray(y_train, dtype=float)
    if train.shape[0] <= season:
        raise ValueError("El entrenamiento debe tener más observaciones que el periodo estacional.")
    scale = np.mean(np.abs(train[season:] - train[:-season]), axis=0)
    if np.any(scale == 0):
        return float("nan")
    return float(np.mean(np.abs(a - b) / scale))
