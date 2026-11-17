"""Análisis exploratorio con series sintéticas de propiedades conocidas."""

import numpy as np
import pandas as pd
import pytest

from forecast_core.eda import cross_correlation as cc
from forecast_core.eda import decomposition as dc
from forecast_core.eda import growth, inflation

IDX = pd.date_range("2013-01-01", periods=120, freq="MS")
SEASON = np.array([0.95, 0.92, 0.98, 0.90, 0.95, 0.96, 1.0, 1.0, 0.97, 1.01, 1.05, 1.31])


def seasonal_series(noise: float = 0.0, seed: int = 0) -> pd.Series:
    rng = np.random.default_rng(seed)
    trend = 100 * 1.04 ** (np.arange(120) / 12)
    season = np.tile(SEASON / SEASON.mean(), 10)
    return pd.Series(trend * season * np.exp(rng.normal(0, noise, 120)), index=IDX, name="y")


def test_descomposicion_recupera_el_patron_estacional() -> None:
    dec = dc.classical_multiplicative(seasonal_series())
    np.testing.assert_allclose(dec.seasonal_index.to_numpy(), SEASON / SEASON.mean(), rtol=2e-3)
    assert dec.seasonal_effect_pct[12] == pytest.approx((1.31 / SEASON.mean() - 1) * 100, abs=0.3)
    assert dc.seasonal_strength(dec) > 0.99


def test_fuerza_estacional_baja_con_ruido_puro() -> None:
    rng = np.random.default_rng(3)
    noise = pd.Series(100 * np.exp(rng.normal(0, 0.05, 120)), index=IDX)
    assert dc.seasonal_strength(dc.classical_multiplicative(noise)) < 0.3


def test_descomposicion_valida_entrada() -> None:
    with pytest.raises(ValueError, match="positivos"):
        dc.classical_multiplicative(pd.Series([-1.0] * 30, index=IDX[:30]))
    with pytest.raises(ValueError, match="dos ciclos"):
        dc.classical_multiplicative(pd.Series([1.0] * 20, index=IDX[:20]))


def test_crecimiento_y_choque() -> None:
    s = seasonal_series()
    assert growth.average_annual_growth(s, 2013, 2022) == pytest.approx(0.04, abs=1e-3)
    s2 = s.copy()
    s2["2020-04-01"] = 10.0
    shock = growth.deepest_shock(s2)
    assert shock.fecha == pd.Timestamp("2020-04-01")
    assert shock.variacion_anual == pytest.approx(10.0 / s2["2019-04-01"] - 1)


def test_brecha_de_inflacion() -> None:
    idx = pd.date_range("2016-12-01", periods=37, freq="MS")
    nacional = pd.Series(100 * 1.003 ** np.arange(37), index=idx)
    local = pd.Series(100 * 1.004 ** np.arange(37), index=idx)
    gap = inflation.inflation_gap(local, nacional)
    assert gap.meses_por_encima == gap.meses_totales == 25
    assert gap.brecha_media == pytest.approx((1.004**12 - 1.003**12) * 100, rel=1e-6)
    assert inflation.cumulative_change(local, "2016-12", "2017-12") == pytest.approx(
        (1.004**12 - 1) * 100
    )


def test_correlacion_cruzada_detecta_el_rezago() -> None:
    rng = np.random.default_rng(7)
    x = pd.Series(rng.normal(size=200), index=pd.date_range("2000-01-01", periods=200, freq="MS"))
    y = x.shift(2) + rng.normal(scale=0.1, size=200)  # x antecede a y en 2 meses
    ccf = cc.cross_correlation(x, y, max_lag=6)
    best = cc.strongest_lag(ccf)
    assert int(best["rezago"]) == 2
    assert best["correlacion"] > 0.9
    assert cc.significance_band(126) == pytest.approx(0.1746, abs=1e-4)


def test_variacion_anual_y_exclusion() -> None:
    s = pd.Series(
        [100.0] * 12 + [110.0] * 12, index=pd.date_range("2019-01-01", periods=24, freq="MS")
    )
    log = cc.yoy_change(s)
    pct = cc.yoy_change(s, method="pct")
    assert log.iloc[-1] == pytest.approx(100 * np.log(1.1))
    assert pct.iloc[-1] == pytest.approx(10.0)
    sin = cc.exclude_periods(pct, [("2020-03", "2020-05")])
    assert sin["2020-03-01":"2020-05-01"].isna().all()
    assert sin["2020-06-01"] == pytest.approx(10.0)
    with pytest.raises(ValueError, match="desconocido"):
        cc.yoy_change(s, method="otro")  # type: ignore[arg-type]
