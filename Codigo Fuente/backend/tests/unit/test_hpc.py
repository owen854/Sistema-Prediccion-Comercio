import numpy as np
import pytest

from forecast_core.features.lags import lag, yoy_log_diff
from forecast_core.features.rolling import rolling_mean
from forecast_core.hpc import benchmark as bm
from forecast_core.hpc import omp
from forecast_core.hpc.mpi import block_partition, mpi_map
from forecast_core.hpc.strategy import SequentialStrategy, get_strategy


def rolling_mean_naive(x: np.ndarray, w: int) -> np.ndarray:
    out = np.full_like(x, np.nan, dtype=float)
    for j in range(x.shape[1]):
        for t in range(w - 1, x.shape[0]):
            out[t, j] = x[t - w + 1 : t + 1, j].mean()
    return out


def test_media_movil_de_referencia(rng: np.random.Generator) -> None:
    x = rng.normal(size=(50, 4))
    x[10, 2] = np.nan
    np.testing.assert_allclose(rolling_mean(x, 5), rolling_mean_naive(x, 5), equal_nan=True)


def test_rezago_y_variacion_anual() -> None:
    x = np.array([[1.0], [2.0], [4.0]])
    assert np.isnan(lag(x, 1)[0, 0])
    assert lag(x, 1)[1:, 0].tolist() == [1.0, 2.0]
    np.testing.assert_allclose(yoy_log_diff(x, 1)[1:, 0], [np.log(2), np.log(2)])


def test_omp_usa_respaldo_numpy(rng: np.random.Generator) -> None:
    x = rng.normal(size=(30, 3))
    np.testing.assert_allclose(
        omp.rolling_mean(x, 4, backend="numpy"), rolling_mean(x, 4), equal_nan=True
    )
    if not omp.KERNELS_AVAILABLE:
        with pytest.raises(RuntimeError, match="forecast_hpc_kernels"):
            omp.rolling_mean(x, 4, backend="openmp")


def test_particion_en_bloques_equilibrados() -> None:
    blocks = block_partition(10, 4)
    assert [len(b) for b in blocks] == [3, 3, 2, 2]
    assert [i for b in blocks for i in b] == list(range(10))
    assert [len(b) for b in block_partition(2, 4)] == [1, 1, 0, 0]


def test_mpi_map_sin_mpi_es_secuencial() -> None:
    class SinMPI:
        def Get_rank(self) -> int:  # noqa: N802 (API de mpi4py)
            return 0

        def Get_size(self) -> int:  # noqa: N802
            return 1

    assert mpi_map(lambda t: t * 2, [1, 2, 3], comm=SinMPI()) == [2, 4, 6]


@pytest.mark.parametrize("error", [ImportError("sin mpi4py"), RuntimeError("cannot load MPI")])
def test_mpi_ausente_no_rompe_la_importacion(
    monkeypatch: pytest.MonkeyPatch, error: Exception
) -> None:
    from forecast_core.hpc import mpi as mpi_mod

    def falla(_: str) -> None:
        raise error

    monkeypatch.setattr(mpi_mod.importlib, "import_module", falla)
    assert mpi_mod._load_mpi() is None


def test_estrategias() -> None:
    assert isinstance(get_strategy("secuencial"), SequentialStrategy)
    assert get_strategy("secuencial").map_tasks(str, [1, 2]) == ["1", "2"]
    with pytest.raises(ValueError, match="Disponibles"):
        get_strategy("cuantica")


def test_metricas_de_rendimiento() -> None:
    assert bm.speedup(10.0, 4.0) == pytest.approx(2.5)
    assert bm.efficiency(10.0, 4.0, 4) == pytest.approx(0.625)
    assert bm.amdahl_speedup(1.0, 8) == pytest.approx(8.0)
    assert bm.amdahl_speedup(0.0, 8) == pytest.approx(1.0)


def test_ajuste_de_amdahl_recupera_f() -> None:
    ps = [1, 2, 4, 8]
    ss = [bm.amdahl_speedup(0.9, p) for p in ps]
    assert bm.fit_amdahl(ps, ss) == pytest.approx(0.9)


def test_time_call_y_hardware() -> None:
    timing = bm.time_call(lambda: sum(range(100)), repeats=3, warmup=0)
    assert len(timing.runs) == 3
    assert timing.minimum <= timing.median <= timing.maximum
    info = bm.hardware_info()
    assert {"sistema", "cpu_logicos", "openmp_kernels", "mpi4py", "gpu_cuda_available"} <= set(info)
