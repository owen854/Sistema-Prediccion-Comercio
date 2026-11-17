"""Generador de datos SINTÉTICOS de ventas minoristas fronterizas.

IMPORTANTE (honestidad metodológica):
    Estos datos existen para (1) desarrollar y probar el pipeline completo y
    (2) medir rendimiento paralelo (speedup) con volumen controlado.
    NO sirven para concluir nada sobre el comercio real de Cúcuta: la relación
    demanda <-> variables fronterizas está puesta por construcción.
    En la monografía hay que declararlo así. Cuando se tengan ventas reales,
    se cargan con data_loader.py y el resto del pipeline no cambia.

Lo que se simula (cada punto con base en el contexto del documento):
    - Nivel base distinto por SKU (log-normal).
    - Estacionalidad semanal (fin de semana alto).
    - Efecto quincena / fin de mes (días 14-17 y 28-2).
    - Estacionalidad anual suave + pico de diciembre.
    - Tendencia leve.
    - Variables exógenas: aforo fronterizo (con cierres), diferencial cambiario
      (spread) y TRM. La TRM puede ser REAL (scripts/00_download_real_data.py la
      baja de datos.gov.co); el aforo y el spread son simulados porque no existe
      una serie diaria pública y limpia de ellos. El nivel base del aforo (~47.000
      personas/día) se tomó de lo reportado por Migración Colombia a inicios de 2026.
    - Ruido de conteo (Poisson): las ventas son enteros >= 0.
"""
from __future__ import annotations

import numpy as np
import pandas as pd


def make_exogenous(dates: pd.DatetimeIndex, rng: np.random.Generator,
                   trm_real: pd.Series | None = None, base_crossings: int = 47_000) -> pd.DataFrame:
    T = len(dates)

    # Aforo fronterizo: AR(1) alrededor de base_crossings cruces/día + cierres
    crossings = np.empty(T)
    crossings[0] = base_crossings
    for t in range(1, T):
        crossings[t] = base_crossings + 0.85 * (crossings[t - 1] - base_crossings) + rng.normal(0, 1_800)
    closed = np.zeros(T, dtype=int)
    n_closures = max(3, T // 250)
    for start in rng.choice(np.arange(30, T - 12), size=n_closures, replace=False):
        length = int(rng.integers(2, 9))
        closed[start:start + length] = 1
    crossings = np.where(closed == 1, crossings * 0.15, crossings)
    # Los fines de semana cruza más gente
    crossings *= np.where(dates.dayofweek >= 4, 1.12, 1.0)

    # Diferencial cambiario (%): caminata aleatoria con reversión a 14 %
    spread = np.empty(T)
    spread[0] = 14.0
    for t in range(1, T):
        spread[t] = spread[t - 1] + 0.05 * (14.0 - spread[t - 1]) + rng.normal(0, 0.45)

    # TRM COP/USD: real si se entrega (datos.gov.co), si no caminata aleatoria
    if trm_real is not None:
        trm = (trm_real.reindex(pd.date_range(dates.min(), dates.max(), freq="D"))
               .ffill().bfill().reindex(dates).to_numpy(dtype=float))
    else:
        trm = 4_000 * np.exp(np.cumsum(rng.normal(0.0001, 0.004, T)))

    return pd.DataFrame({
        "date": dates,
        "border_crossings": crossings.round().astype(int),
        "border_closed": closed,
        "ves_spread_pct": spread.round(2),
        "trm_cop_usd": trm.round(1),
    })


def make_sales(exog: pd.DataFrame, n_series: int, rng: np.random.Generator,
               base_crossings: int = 47_000) -> pd.DataFrame:
    dates = pd.DatetimeIndex(exog["date"])
    T = len(dates)
    t = np.arange(T)
    dow = dates.dayofweek.values
    dom = dates.day.values
    doy = dates.dayofyear.values

    weekly = np.array([0.94, 0.97, 1.00, 1.03, 1.12, 1.22, 0.80])[dow]
    quincena = np.where(((dom >= 14) & (dom <= 17)) | (dom >= 28) | (dom <= 2), 1.18, 1.0)
    annual = 1 + 0.06 * np.sin(2 * np.pi * doy / 365.25) + np.where(dates.month == 12, 0.12, 0.0)

    cross_rel = exog["border_crossings"].values / base_crossings
    spread_dev = (exog["ves_spread_pct"].values - 14.0) / 14.0
    trm = exog["trm_cop_usd"]
    trm_dev = (trm / trm.rolling(90, min_periods=1).mean() - 1.0).to_numpy()  # desvío vs. su media de 90 d

    categories = ["Canasta Familiar", "Salud y Farmacia", "Cuidado Personal",
                  "Ferretería y Repuestos", "Otros"]
    rows = []
    for i in range(n_series):
        base = float(rng.lognormal(mean=np.log(60), sigma=0.6))
        trend = 1 + rng.normal(0.0002, 0.0001) * t
        beta_cross = rng.uniform(0.25, 0.9)      # sensibilidad al aforo
        beta_fx = rng.uniform(-0.3, 0.5)         # sensibilidad al spread
        beta_trm = rng.uniform(-1.0, 1.0)        # sensibilidad a la TRM
        lam = base * weekly * quincena * annual * trend \
              * np.power(np.clip(cross_rel, 0.05, None), beta_cross) \
              * (1 + beta_fx * spread_dev) * (1 + beta_trm * trm_dev)
        units = rng.poisson(np.clip(lam, 0.1, None))
        rows.append(pd.DataFrame({
            "date": dates,
            "series_id": f"SKU{i:04d}",
            "category": categories[i % len(categories)],
            "units": units.astype(int),
        }))
    return pd.concat(rows, ignore_index=True)


def generate(n_series: int = 60, start: str = "2023-01-01", end: str = "2026-11-06",
             seed: int = 42, trm_real: pd.Series | None = None,
             base_crossings: int = 47_000) -> tuple[pd.DataFrame, pd.DataFrame]:
    rng = np.random.default_rng(seed)
    dates = pd.date_range(start, end, freq="D")
    exog = make_exogenous(dates, rng, trm_real, base_crossings)
    sales = make_sales(exog, n_series, rng, base_crossings)
    return sales, exog
