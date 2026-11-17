"""Ingesta del índice de ventas reales de la Encuesta Mensual de Comercio del DANE (RF-01).

Lee el anexo "Series índices empalmados comercio al por menor" (hoja 1.2: valores
reales, base 2019 = 100) y devuelve la serie mensual de la columna configurada
(por defecto, "Total comercio minorista sin otros vehículos", la del informe).
"""

from __future__ import annotations

from pathlib import Path

import openpyxl
import pandas as pd

from forecast_core.ingestion.common import normalize_text, parse_spanish_month

DEFAULT_SHEET = "1.2"
DEFAULT_COLUMN = "Total comercio minorista sin otros vehículos"


def parse_emc_index(
    path: str | Path, *, sheet: str = DEFAULT_SHEET, column: str = DEFAULT_COLUMN
) -> pd.Series:
    """Serie mensual (inicio de mes) del índice de la columna ``column``.

    La tabla tiene una fila de encabezados con "Año" y "Mes"; el año aparece solo
    en enero y se arrastra a los meses siguientes. La lectura termina en la primera
    fila cuyo mes no es un nombre de mes (notas al pie).
    """
    wb = openpyxl.load_workbook(path, read_only=True, data_only=True)
    try:
        rows = list(wb[sheet].iter_rows(values_only=True))
    finally:
        wb.close()

    header_idx, header = _find_header(rows)
    norm = [normalize_text(h) if h is not None else "" for h in header]
    year_col, month_col = norm.index("ano"), norm.index("mes")
    try:
        value_col = norm.index(normalize_text(column))
    except ValueError:
        raise ValueError(f"La hoja {sheet} no tiene la columna {column!r}.") from None

    dates, values = [], []
    year: int | None = None
    for row in rows[header_idx + 1 :]:
        if row[year_col] not in (None, ""):
            try:
                year = int(float(str(row[year_col])))
            except ValueError:
                break
        month = parse_spanish_month(row[month_col])
        if month is None or year is None:
            break
        dates.append(pd.Timestamp(year=year, month=month, day=1))
        values.append(float(row[value_col]))

    index = pd.DatetimeIndex(dates)
    if index.has_duplicates:
        raise ValueError("El anexo tiene meses repetidos.")
    expected = pd.date_range(index.min(), index.max(), freq="MS")
    missing = expected.difference(index)
    if len(missing):
        raise ValueError(f"Al anexo le faltan meses: {[d.strftime('%Y-%m') for d in missing]}.")
    return pd.Series(values, index=expected, name="emc_ventas_reales")


def _find_header(rows: list[tuple[object, ...]]) -> tuple[int, tuple[object, ...]]:
    for i, row in enumerate(rows):
        cells = {normalize_text(v) for v in row if v is not None}
        if {"ano", "mes"} <= cells:
            return i, row
    raise ValueError("No se encontró la fila de encabezados (Año, Mes).")
