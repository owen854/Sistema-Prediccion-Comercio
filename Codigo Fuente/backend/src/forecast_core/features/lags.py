"""Rezagos y variaciones por serie: implementación secuencial de referencia (RF-15, RF-34)."""

from __future__ import annotations

import numpy as np


def lag(values: np.ndarray, k: int) -> np.ndarray:
    """Desplaza cada columna ``k`` periodos; las primeras ``k`` filas quedan en NaN."""
    if k < 0:
        raise ValueError("k debe ser mayor o igual a 0.")
    arr = np.asarray(values, dtype=np.float64)
    if arr.ndim != 2:
        raise ValueError("values debe ser una matriz (T, N).")
    out = np.full_like(arr, np.nan)
    if k < arr.shape[0]:
        out[k:] = arr[: arr.shape[0] - k]
    return out


def yoy_log_diff(values: np.ndarray, period: int) -> np.ndarray:
    """Variación del logaritmo frente al mismo periodo del año anterior.

    Es la variable objetivo del piloto LSTM del informe (``period=12`` en datos
    mensuales). Los valores no positivos producen ``NaN``.
    """
    arr = np.asarray(values, dtype=np.float64)
    with np.errstate(divide="ignore", invalid="ignore"):
        logs = np.where(arr > 0, np.log(np.where(arr > 0, arr, 1.0)), np.nan)
    result: np.ndarray = logs - lag(logs, period)
    return result
