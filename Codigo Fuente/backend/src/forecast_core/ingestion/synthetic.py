"""Generador de datos SINTÉTICOS de ventas minoristas fronterizas (RF-10).

Migrado de ``Prototipo/demand-forecast-hpc/src/data_generation.py`` conservando el
mismo orden de llamadas al generador aleatorio: con la misma semilla produce
exactamente los mismos datos que el prototipo (lo verifica
``tests/equivalence/test_regresion_prototipo.py``).

IMPORTANTE (honestidad metodológica):
    Estos datos existen para (1) desarrollar y probar el pipeline completo y
    (2) medir el rendimiento paralelo con volumen controlado. NO sirven para
    concluir nada sobre el comercio real de Cúcuta: la relación entre la demanda
    y las variables fronterizas está puesta por construcción. Toda fila lleva la
    columna ``origin = "sintetico"`` y así se muestra en reportes e interfaz.

Lo que se simula:
    - Nivel base distinto por SKU (log-normal).
    - Estacionalidad semanal (fin de semana alto).
    - Efecto quincena y fin de mes (días 14-17 y 28-2).
    - Estacionalidad anual suave y pico de diciembre.
    - Tendencia leve.
    - Exógenas: aforo fronterizo con cierres, diferencial cambiario y TRM (la TRM
      puede ser real; ver ``ingestion.trm``).
    - Ruido de conteo (Poisson): ventas enteras mayores o iguales a 0.
"""

from __future__ import annotations

import numpy as np
import pandas as pd

from forecast_core.types import DataOrigin

CATEGORIES = (
    "Canasta Familiar",
    "Salud y Farmacia",
    "Cuidado Personal",
    "Ferretería y Repuestos",
    "Otros",
)
BASE_CROSSINGS = 47_000  # personas/día; nivel reportado por Migración Colombia a inicios de 2026


def make_exogenous(
    dates: pd.DatetimeIndex,
    rng: np.random.Generator,
    trm_real: pd.Series | None = None,
    base_crossings: int = BASE_CROSSINGS,
) -> pd.DataFrame:
    """Simula las variables exógenas diarias (aforo, cierres, diferencial y TRM)."""
    T = len(dates)

    # Aforo fronterizo: AR(1) alrededor de base_crossings cruces/día + cierres
    crossings = np.empty(T)
    crossings[0] = base_crossings
    for t in range(1, T):
        crossings[t] = (
            base_crossings + 0.85 * (crossings[t - 1] - base_crossings) + rng.normal(0, 1_800)
        )
    closed = np.zeros(T, dtype=int)
    n_closures = max(3, T // 250)
    for start in rng.choice(np.arange(30, T - 12), size=n_closures, replace=False):
        length = int(rng.integers(2, 9))
        closed[start : start + length] = 1
    crossings = np.where(closed == 1, crossings * 0.15, crossings)
    # Los fines de semana cruza más gente
    crossings *= np.where(dates.day_of_week >= 4, 1.12, 1.0)

    # Diferencial cambiario (%): caminata aleatoria con reversión a 14 %
    spread = np.empty(T)
    spread[0] = 14.0
    for t in range(1, T):
        spread[t] = spread[t - 1] + 0.05 * (14.0 - spread[t - 1]) + rng.normal(0, 0.45)

    # TRM COP/USD: real si se entrega, si no caminata aleatoria
    if trm_real is not None:
        trm = (
            trm_real.reindex(pd.date_range(dates.min(), dates.max(), freq="D"))
            .ffill()
            .bfill()
            .reindex(dates)
            .to_numpy(dtype=float)
        )
    else:
        trm = 4_000 * np.exp(np.cumsum(rng.normal(0.0001, 0.004, T)))

    return pd.DataFrame(
        {
            "date": dates,
            "border_crossings": crossings.round().astype(int),
            "border_closed": closed,
            "ves_spread_pct": spread.round(2),
            "trm_cop_usd": trm.round(1),
            "origin": DataOrigin.SINTETICO.value,
        }
    )


def make_sales(
    exog: pd.DataFrame,
    n_series: int,
    rng: np.random.Generator,
    base_crossings: int = BASE_CROSSINGS,
) -> pd.DataFrame:
    """Simula las ventas diarias de ``n_series`` productos a partir de las exógenas."""
    dates = pd.DatetimeIndex(exog["date"])
    T = len(dates)
    t = np.arange(T)
    dow = dates.day_of_week.to_numpy()
    dom = dates.day.to_numpy()
    doy = dates.day_of_year.to_numpy()

    weekly = np.array([0.94, 0.97, 1.00, 1.03, 1.12, 1.22, 0.80])[dow]
    quincena = np.where(((dom >= 14) & (dom <= 17)) | (dom >= 28) | (dom <= 2), 1.18, 1.0)
    annual = 1 + 0.06 * np.sin(2 * np.pi * doy / 365.25) + np.where(dates.month == 12, 0.12, 0.0)

    cross_rel = exog["border_crossings"].to_numpy() / base_crossings
    spread_dev = (exog["ves_spread_pct"].to_numpy() - 14.0) / 14.0
    trm = exog["trm_cop_usd"]
    trm_dev = (trm / trm.rolling(90, min_periods=1).mean() - 1.0).to_numpy()

    rows = []
    for i in range(n_series):
        base = float(rng.lognormal(mean=np.log(60), sigma=0.6))
        trend = 1 + rng.normal(0.0002, 0.0001) * t
        beta_cross = rng.uniform(0.25, 0.9)  # sensibilidad al aforo
        beta_fx = rng.uniform(-0.3, 0.5)  # sensibilidad al diferencial
        beta_trm = rng.uniform(-1.0, 1.0)  # sensibilidad a la TRM
        lam = (
            base
            * weekly
            * quincena
            * annual
            * trend
            * np.power(np.clip(cross_rel, 0.05, None), beta_cross)
            * (1 + beta_fx * spread_dev)
            * (1 + beta_trm * trm_dev)
        )
        units = rng.poisson(np.clip(lam, 0.1, None))
        rows.append(
            pd.DataFrame(
                {
                    "date": dates,
                    "series_id": f"SKU{i:04d}",
                    "category": CATEGORIES[i % len(CATEGORIES)],
                    "units": units.astype(int),
                    "origin": DataOrigin.SINTETICO.value,
                }
            )
        )
    return pd.concat(rows, ignore_index=True)


def generate(
    n_series: int = 60,
    start: str = "2023-01-01",
    end: str = "2026-11-06",
    seed: int = 42,
    trm_real: pd.Series | None = None,
    base_crossings: int = BASE_CROSSINGS,
) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Genera ``(ventas, exogenas)`` sintéticas.

    Las fechas son explícitas (no dependen del día de ejecución) para que el
    resultado sea reproducible (corrige el hallazgo A4 de la evaluación).
    """
    rng = np.random.default_rng(seed)
    dates = pd.date_range(start, end, freq="D")
    exog = make_exogenous(dates, rng, trm_real, base_crossings)
    sales = make_sales(exog, n_series, rng, base_crossings)
    return sales, exog
