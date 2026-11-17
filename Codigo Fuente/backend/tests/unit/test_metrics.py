import math

import numpy as np
import pytest
from hypothesis import given
from hypothesis import strategies as st
from hypothesis.extra.numpy import arrays

from forecast_core.evaluation import metrics as m


def test_valores_conocidos() -> None:
    y = np.array([10.0, 20.0, 30.0, 40.0])
    yhat = np.array([12.0, 18.0, 33.0, 40.0])
    assert m.mae(y, yhat) == pytest.approx(7 / 4)
    assert m.rmse(y, yhat) == pytest.approx(math.sqrt((4 + 4 + 9 + 0) / 4))
    assert m.mape(y, yhat) == pytest.approx(100 * (0.2 + 0.1 + 0.1 + 0) / 4)
    assert m.wape(y, yhat) == pytest.approx(100 * 7 / 100)


def test_mape_excluye_ceros_y_los_reporta() -> None:
    y = np.array([0.0, 10.0, 0.0, 20.0])
    yhat = np.array([5.0, 11.0, 1.0, 18.0])
    assert m.mape(y, yhat) == pytest.approx(100 * (0.1 + 0.1) / 2)
    assert m.n_zero_excluded(y) == 2


def test_mape_todo_ceros_es_nan() -> None:
    assert math.isnan(m.mape([0, 0], [1, 2]))


def test_smape_es_simetrico() -> None:
    assert m.smape([100], [110]) == pytest.approx(m.smape([110], [100]))


def test_mase_menor_que_uno_si_mejora_al_ingenuo() -> None:
    train = np.array([1.0, 2.0, 3.0, 4.0, 5.0])  # escala del ingenuo (m=1): 1.0
    assert m.mase([6.0, 7.0], [6.2, 6.9], train, season=1) == pytest.approx(0.15)


def test_mase_por_series_en_matriz() -> None:
    train = np.array([[1.0, 10.0], [2.0, 30.0], [3.0, 50.0]])  # escalas 1 y 20
    y = np.array([[4.0, 70.0]])
    yhat = np.array([[5.0, 50.0]])
    assert m.mase(y, yhat, train) == pytest.approx((1 / 1 + 20 / 20) / 2)


def test_formas_distintas_falla() -> None:
    with pytest.raises(ValueError, match="Formas distintas"):
        m.rmse([1, 2], [1, 2, 3])


@given(
    arrays(np.float64, 20, elements=st.floats(-1e6, 1e6)),
    arrays(np.float64, 20, elements=st.floats(-1e6, 1e6)),
)
def test_rmse_mayor_o_igual_que_mae(y: np.ndarray, yhat: np.ndarray) -> None:
    assert m.rmse(y, yhat) >= m.mae(y, yhat) - 1e-9 >= -1e-9
