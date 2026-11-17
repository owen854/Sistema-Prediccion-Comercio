"""Medición de rendimiento paralelo (RF-40).

* Aceleración: ``S(p) = T1 / Tp``
* Eficiencia: ``E(p) = S(p) / p``
* Ley de Amdahl: ``S(p) ≤ 1 / ((1 − f) + f / p)``, donde ``f`` es la fracción
  paralelizable. :func:`fit_amdahl` estima ``f`` a partir de las mediciones.

Regla del proyecto (``05_Entorno_Desarrollo_HPC.md``): T1 y Tp se miden en la misma
máquina y cada configuración se repite varias veces; se reporta la mediana.
"""

from __future__ import annotations

import os
import platform
import statistics
import time
from collections.abc import Callable, Sequence
from dataclasses import asdict, dataclass
from typing import Any

import numpy as np


@dataclass(frozen=True)
class Timing:
    """Tiempos de varias repeticiones, en segundos."""

    runs: tuple[float, ...]

    @property
    def median(self) -> float:
        return statistics.median(self.runs)

    @property
    def minimum(self) -> float:
        return min(self.runs)

    @property
    def maximum(self) -> float:
        return max(self.runs)

    def as_dict(self) -> dict[str, Any]:
        return {**asdict(self), "median": self.median, "min": self.minimum, "max": self.maximum}


def time_call(fn: Callable[[], object], repeats: int = 5, warmup: int = 1) -> Timing:
    """Ejecuta ``fn`` ``warmup`` veces sin medir y ``repeats`` veces midiendo."""
    if repeats < 1:
        raise ValueError("repeats debe ser mayor o igual a 1.")
    for _ in range(warmup):
        fn()
    runs = []
    for _ in range(repeats):
        start = time.perf_counter()
        fn()
        runs.append(time.perf_counter() - start)
    return Timing(tuple(runs))


def speedup(t1: float, tp: float) -> float:
    if tp <= 0:
        raise ValueError("Tp debe ser positivo.")
    return t1 / tp


def efficiency(t1: float, tp: float, p: int) -> float:
    if p < 1:
        raise ValueError("p debe ser mayor o igual a 1.")
    return speedup(t1, tp) / p


def amdahl_speedup(f: float, p: int) -> float:
    """Aceleración máxima teórica con fracción paralelizable ``f`` y ``p`` unidades."""
    if not 0.0 <= f <= 1.0:
        raise ValueError("f debe estar entre 0 y 1.")
    return 1.0 / ((1.0 - f) + f / p)


def fit_amdahl(p_values: Sequence[float], speedups: Sequence[float]) -> float:
    """Estima ``f`` por mínimos cuadrados con la forma lineal ``1/S − 1 = f (1/p − 1)``."""
    p = np.asarray(p_values, dtype=float)
    s = np.asarray(speedups, dtype=float)
    mask = p > 1
    if not mask.any():
        raise ValueError("Se necesita al menos una medición con p > 1.")
    a = 1.0 / p[mask] - 1.0
    b = 1.0 / s[mask] - 1.0
    f = float(np.dot(a, b) / np.dot(a, a))
    return min(max(f, 0.0), 1.0)


def hardware_info() -> dict[str, Any]:
    """Describe el equipo donde se mide; se guarda con cada resultado."""
    from forecast_core.hpc import cuda, omp
    from forecast_core.hpc import mpi as mpi_mod

    info: dict[str, Any] = {
        "sistema": platform.platform(),
        "procesador": platform.processor() or platform.machine(),
        "cpu_logicos": os.cpu_count(),
        "python": platform.python_version(),
        "numpy": np.__version__,
        "openmp_kernels": omp.KERNELS_AVAILABLE,
        "openmp_max_hilos": omp.max_threads(),
        "mpi4py": mpi_mod.MPI_AVAILABLE,
    }
    if (version := mpi_mod.library_version()) is not None:
        info["mpi_libreria"] = version
    try:
        with open("/proc/meminfo", encoding="ascii") as fh:
            total_kb = int(fh.readline().split()[1])
        info["ram_gb"] = round(total_kb / 1024**2, 1)
    except (OSError, ValueError, IndexError):
        pass
    info.update({f"gpu_{k}": v for k, v in cuda.cuda_info().items()})
    return info
