"""Núcleos OpenMP ≡ referencia secuencial en NumPy (RF-39).

Se ejecuta donde está compilado ``forecast_hpc_kernels`` (WSL, Colab, CI).
"""

import numpy as np
import pytest

from forecast_core.features.lags import lag
from forecast_core.features.rolling import rolling_mean
from forecast_core.hpc import omp

pytestmark = [
    pytest.mark.kernels,
    pytest.mark.skipif(not omp.KERNELS_AVAILABLE, reason="forecast_hpc_kernels no compilado"),
]


@pytest.mark.parametrize("threads", [1, 2, 4, 8])
@pytest.mark.parametrize("window", [1, 7, 28])
def test_media_movil_equivalente(rng: np.random.Generator, threads: int, window: int) -> None:
    x = rng.gamma(2.0, 30.0, size=(400, 37))
    x[rng.integers(0, 400, 20), rng.integers(0, 37, 20)] = np.nan
    np.testing.assert_allclose(
        omp.rolling_mean(x, window, threads=threads, backend="openmp"),
        rolling_mean(x, window),
        rtol=1e-9,
        atol=1e-9,
        equal_nan=True,
    )


def test_resultado_identico_con_cualquier_numero_de_hilos(rng: np.random.Generator) -> None:
    x = rng.normal(size=(1000, 64))
    uno = omp.rolling_mean(x, 14, threads=1, backend="openmp")
    for h in (2, 4, 8):
        np.testing.assert_array_equal(omp.rolling_mean(x, 14, threads=h, backend="openmp"), uno)


@pytest.mark.parametrize("k", [0, 1, 12, 500])
def test_rezago_equivalente(rng: np.random.Generator, k: int) -> None:
    x = rng.normal(size=(300, 9))
    np.testing.assert_array_equal(omp.lag(x, k, threads=4, backend="openmp"), lag(x, k))


def test_acepta_matrices_en_orden_c_y_fortran(rng: np.random.Generator) -> None:
    x = rng.normal(size=(50, 6))
    a = omp.rolling_mean(np.ascontiguousarray(x), 5, backend="openmp")
    b = omp.rolling_mean(np.asfortranarray(x), 5, backend="openmp")
    np.testing.assert_array_equal(a, b)
