"""Carga de datos y conversión a formato matricial.

Formato esperado de las ventas REALES (CSV):
    date,series_id,units
    2024-03-01,SKU_ARROZ_500G,34
    ...
Formato esperado de las exógenas (CSV, una fila por día):
    date,border_crossings,border_closed,ves_spread_pct,trm_cop_usd

Por qué una matriz (T días x N series): es el formato que usarán después
OpenMP/MPI (repartir columnas = series entre hilos/procesos) y CUDA/PyTorch
(tensores en GPU). Conviene fijarlo desde ahora.
"""
from __future__ import annotations

import numpy as np
import pandas as pd


def load_csv(sales_path: str, exog_path: str) -> tuple[pd.DataFrame, pd.DataFrame]:
    sales = pd.read_csv(sales_path, parse_dates=["date"])
    exog = pd.read_csv(exog_path, parse_dates=["date"])
    return sales, exog


def to_matrix(sales: pd.DataFrame) -> tuple[np.ndarray, pd.DatetimeIndex, list[str]]:
    """Long -> wide. Días sin registro de una serie se rellenan con 0 (no hubo venta).

    Devuelve (Y, fechas, ids) con Y de forma (T, N).
    """
    wide = sales.pivot_table(index="date", columns="series_id", values="units",
                             aggfunc="sum").sort_index()
    full_idx = pd.date_range(wide.index.min(), wide.index.max(), freq="D")
    wide = wide.reindex(full_idx).fillna(0)
    return wide.to_numpy(dtype=float), wide.index, list(wide.columns)


def quality_report(sales: pd.DataFrame) -> dict:
    """Fase 1 (CRISP-DM, comprensión de los datos): completitud y consistencia."""
    return {
        "filas": len(sales),
        "series": sales["series_id"].nunique(),
        "fecha_inicio": str(sales["date"].min().date()),
        "fecha_fin": str(sales["date"].max().date()),
        "dias_cubiertos": int((sales["date"].max() - sales["date"].min()).days + 1),
        "nulos": int(sales["units"].isna().sum()),
        "negativos": int((sales["units"] < 0).sum()),
        "pct_ceros": round(float((sales["units"] == 0).mean() * 100), 2),
    }
