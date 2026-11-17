"""Núcleos C++ con OpenMP para paneles T×N (RF-35; ADR-003).

Se usan a través de ``forecast_core.hpc.omp``, que cae a NumPy si este módulo no
está compilado.
"""

from forecast_hpc_kernels._core import lag, max_threads, openmp_version, rolling_mean

__all__ = ["lag", "max_threads", "openmp_version", "rolling_mean"]
