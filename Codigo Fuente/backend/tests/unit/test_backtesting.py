import pytest
from hypothesis import given
from hypothesis import strategies as st

from forecast_core.evaluation.backtesting import Fold, check_no_leakage, rolling_origin_folds


def test_ultima_particion_termina_en_n_obs() -> None:
    folds = list(rolling_origin_folds(100, horizon=14, n_folds=6))
    assert len(folds) == 6
    assert folds[-1].test_end == 100
    assert all(f.horizon == 14 for f in folds)


def test_paso_distinto_del_horizonte() -> None:
    folds = list(rolling_origin_folds(200, horizon=14, n_folds=4, step=7))
    assert [f.train_end for f in folds] == [165, 172, 179, 186]


def test_serie_corta_falla() -> None:
    with pytest.raises(ValueError, match="demasiado corta"):
        list(rolling_origin_folds(20, horizon=14, n_folds=3))


def test_detecta_particion_invalida() -> None:
    with pytest.raises(ValueError, match="inválida"):
        check_no_leakage([Fold(0, train_end=10, test_end=10)], n_obs=20)


@given(
    n_obs=st.integers(30, 2000),
    horizon=st.integers(1, 30),
    n_folds=st.integers(1, 10),
    step=st.integers(1, 30),
)
def test_nunca_hay_fuga_de_informacion(n_obs: int, horizon: int, n_folds: int, step: int) -> None:
    try:
        folds = list(rolling_origin_folds(n_obs, horizon, n_folds, step))
    except ValueError:
        return
    check_no_leakage(folds, n_obs)
    for f in folds:
        # Ninguna fecha de prueba aparece en el entrenamiento
        assert set(range(f.train_end)).isdisjoint(range(f.train_end, f.test_end))
