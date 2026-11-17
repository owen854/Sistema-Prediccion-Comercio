"""Puente a los núcleos C++ con OpenMP (RF-35; ADR-003).

Si el módulo compilado ``forecast_hpc_kernels`` está instalado (WSL, Colab, CI),
los cálculos se hacen en C++ con varios hilos. Si no (por ejemplo, en Windows),
se usa la implementación de referencia en NumPy con la misma interfaz (RNF-13).
"""

from __future__ import annotations

import importlib
from typing import Any, Literal

import numpy as np

from forecast_core.features import lags as _ref_lags
from forecast_core.features import rolling as _ref_rolling


def _load_kernels() -> Any:
    """Importa ``forecast_hpc_kernels`` si está compilado (mismo tipo en todo sistema)."""
    try:
        return importlib.import_module("forecast_hpc_kernels")
    except ImportError:  # pragma: no cover - depende del entorno
        return None


_kernels: Any = _load_kernels()
KERNELS_AVAILABLE = _kernels is not None

Backend = Literal["auto", "numpy", "openmp"]


def _use_kernels(backend: Backend) -> bool:
    if backend == "numpy":
        return False
    if backend == "openmp":
        if not KERNELS_AVAILABLE:
            raise RuntimeError(
                "El backend 'openmp' requiere el módulo compilado forecast_hpc_kernels "
                "(instálelo en WSL/Linux con: uv sync --extra kernels)."
            )
        return True
    if backend == "auto":
        return KERNELS_AVAILABLE
    raise ValueError(f"Backend desconocido: {backend!r}.")


def max_threads() -> int:
    """Hilos OpenMP disponibles (1 si no hay núcleos compilados)."""
    return int(_kernels.max_threads()) if KERNELS_AVAILABLE and _kernels else 1


def rolling_mean(
    values: np.ndarray, window: int, *, threads: int = 0, backend: Backend = "auto"
) -> np.ndarray:
    """Media móvil por serie. ``threads=0`` usa el valor por defecto de OpenMP."""
    if _use_kernels(backend) and _kernels is not None:
        return np.asarray(_kernels.rolling_mean(values, window, threads))
    return _ref_rolling.rolling_mean(values, window)


def lag(values: np.ndarray, k: int, *, threads: int = 0, backend: Backend = "auto") -> np.ndarray:
    """Rezago ``k`` por serie."""
    if _use_kernels(backend) and _kernels is not None:
        return np.asarray(_kernels.lag(values, k, threads))
    return _ref_lags.lag(values, k)
