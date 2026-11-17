"""Medias móviles por serie: implementación secuencial de referencia (RF-15, RF-34).

Es la referencia contra la que se comparan los núcleos OpenMP
(``hpc_kernels/src/features_omp.cpp``) en las pruebas de equivalencia (RF-39).

Semántica: la media en ``t`` usa ``[t - window + 1, t]``; es ``NaN`` si faltan
periodos al inicio o si hay algún ``NaN`` dentro de la ventana (y se recupera
cuando el ``NaN`` sale de la ventana). Es la misma que
``pandas.DataFrame.rolling(window, min_periods=window).mean()``.
"""

from __future__ import annotations

import numpy as np
import pandas as pd


def rolling_mean(values: np.ndarray, window: int) -> np.ndarray:
    """Media móvil de cada columna de una matriz ``(T, N)``."""
    if window < 1:
        raise ValueError("window debe ser mayor o igual a 1.")
    arr = np.asarray(values, dtype=np.float64)
    if arr.ndim != 2:
        raise ValueError("values debe ser una matriz (T, N).")
    out = pd.DataFrame(arr).rolling(window, min_periods=window).mean().to_numpy()
    return np.asarray(out, dtype=np.float64)
