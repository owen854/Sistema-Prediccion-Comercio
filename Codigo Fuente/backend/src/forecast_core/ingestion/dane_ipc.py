"""Ingesta del IPC por ciudades (RF-02).

* :func:`parse_city_monthly_variation` lee la hoja "4" del anexo mensual del DANE
  (``anex-IPC-<mes><año>.xlsx``): variación mensual del total por ciudad, **solo
  para el mes publicado**.
* :func:`load_city_history_csv` carga la historia mensual por ciudad desde un CSV
  ``fecha, ciudad, variacion_pct`` (formato del archivo histórico del informe).
* :func:`index_from_monthly_variation` reconstruye el índice (dic-2016 = 100) a
  partir de las variaciones mensuales, como hizo el informe.
"""

from __future__ import annotations

import re
from pathlib import Path

import openpyxl
import pandas as pd

from forecast_core.ingestion.common import SPANISH_MONTHS, normalize_text

MONTH_TITLE = re.compile(r"^([a-z]+) de (\d{4})$")


def parse_city_monthly_variation(path: str | Path, *, sheet: str = "4") -> pd.Series:
    """Variación mensual (%) del IPC total por ciudad para el mes del anexo.

    Devuelve una serie indexada por ciudad (incluye ``"Total IPC"`` = nacional) con
    el atributo ``attrs["fecha"]`` (inicio del mes publicado).
    """
    wb = openpyxl.load_workbook(path, read_only=True, data_only=True)
    try:
        rows = list(wb[sheet].iter_rows(values_only=True))
    finally:
        wb.close()

    fecha: pd.Timestamp | None = None
    header_idx = -1
    for i, row in enumerate(rows):
        first = normalize_text(row[0]) if row and row[0] is not None else ""
        match = MONTH_TITLE.match(first)
        if match and match.group(1) in SPANISH_MONTHS:
            fecha = pd.Timestamp(
                year=int(match.group(2)), month=SPANISH_MONTHS[match.group(1)], day=1
            )
        if first == "ciudades":
            header_idx = i
            break
    if header_idx < 0 or fecha is None:
        raise ValueError("No se encontró el mes o la fila de encabezados 'Ciudades'.")

    header = [normalize_text(h) if h is not None else "" for h in rows[header_idx]]
    total_cols = [j for j, h in enumerate(header) if h == "total"]
    if not total_cols:
        raise ValueError("La hoja no tiene la columna 'Total'.")
    total_col = total_cols[-1]

    data: dict[str, float] = {}
    for row in rows[header_idx + 1 :]:
        if not row or row[0] is None or row[total_col] is None:
            break
        data[str(row[0]).strip()] = float(row[total_col])
    series = pd.Series(data, name="variacion_mensual_pct", dtype=float)
    series.attrs["fecha"] = fecha
    return series


def load_city_history_csv(path: str | Path) -> pd.DataFrame:
    """Historia de variaciones mensuales: DataFrame fechas × ciudades (en %)."""
    df = pd.read_csv(path, parse_dates=["fecha"])
    missing = {"fecha", "ciudad", "variacion_pct"} - set(df.columns)
    if missing:
        raise ValueError(f"Faltan columnas en {path}: {sorted(missing)}.")
    wide = df.pivot_table(index="fecha", columns="ciudad", values="variacion_pct", aggfunc="first")
    wide.index = pd.DatetimeIndex(wide.index).to_period("M").to_timestamp()
    return wide.sort_index()


def index_from_monthly_variation(
    variation_pct: pd.Series, *, base_date: str = "2016-12", base_value: float = 100.0
) -> pd.Series:
    """Índice encadenado: ``I_base = base_value`` e ``I_t = I_{t-1} · (1 + v_t / 100)``."""
    base = pd.Timestamp(f"{base_date}-01")
    v = variation_pct.sort_index()
    if v.index.min() <= base:
        raise ValueError("Las variaciones deben empezar después del mes base.")
    factors = 1 + v / 100.0
    index = base_value * factors.cumprod()
    full = pd.concat([pd.Series([base_value], index=[base]), index])
    return pd.Series(
        full.to_numpy(), index=pd.DatetimeIndex(full.index, freq="MS"), name=variation_pct.name
    )
