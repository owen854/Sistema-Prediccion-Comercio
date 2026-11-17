"""Reporte de calidad de datos (RF-07; CRISP-DM, comprensión de los datos).

Migrado y ampliado desde ``data_loader.quality_report`` del prototipo: además de
filas, series, cobertura, nulos, negativos y ceros, reporta duplicados y celdas
faltantes en la rejilla completa fechas × series (hallazgo A8 de la evaluación).
"""

from __future__ import annotations

from typing import Any

import pandas as pd


def quality_report(
    df: pd.DataFrame,
    *,
    date_col: str = "date",
    series_col: str = "series_id",
    value_col: str = "units",
    freq: str = "D",
) -> dict[str, Any]:
    """Calcula los indicadores de calidad de un conjunto de datos en formato largo.

    Returns
    -------
    dict
        ``filas``, ``series``, ``fecha_inicio``, ``fecha_fin``, ``periodos_cubiertos``,
        ``nulos``, ``negativos``, ``duplicados``, ``pct_ceros``, ``celdas_faltantes``
        y ``pct_celdas_faltantes``.
    """
    if df.empty:
        raise ValueError("El conjunto de datos está vacío.")
    dates = pd.to_datetime(df[date_col])
    values = df[value_col]
    start, end = dates.min(), dates.max()
    n_periods = len(pd.date_range(start, end, freq=freq))
    n_series = int(df[series_col].nunique())

    duplicated = int(df.duplicated(subset=[date_col, series_col]).sum())
    present_cells = int(df.drop_duplicates(subset=[date_col, series_col]).shape[0])
    expected_cells = n_periods * n_series
    missing_cells = max(expected_cells - present_cells, 0)

    return {
        "filas": len(df),
        "series": n_series,
        "fecha_inicio": str(start.date()),
        "fecha_fin": str(end.date()),
        "periodos_cubiertos": n_periods,
        "nulos": int(values.isna().sum()),
        "negativos": int((values < 0).sum()),
        "duplicados": duplicated,
        "pct_ceros": round(float((values == 0).mean() * 100), 2),
        "celdas_faltantes": missing_cells,
        "pct_celdas_faltantes": round(100 * missing_cells / expected_cells, 2),
    }
