"""Construcción del panel alineado T periodos × N series (RF-14).

Migrado de ``data_loader.to_matrix`` del prototipo. Cambio principal (hallazgo A7):
el relleno de periodos sin registro es configurable y se cuenta, porque "no hubo
venta" (0) no es lo mismo que "no hay dato" (``NaN``: tienda cerrada o registro
faltante).
"""

from __future__ import annotations

from typing import Literal

import numpy as np
import pandas as pd

from forecast_core.types import DataOrigin, Panel

FillRule = Literal["zero", "nan"]


def to_panel(
    df: pd.DataFrame,
    *,
    date_col: str = "date",
    series_col: str = "series_id",
    value_col: str = "units",
    freq: str = "D",
    fill: FillRule = "zero",
    origin: DataOrigin | None = None,
) -> Panel:
    """Convierte datos en formato largo a un :class:`Panel`.

    Los registros repetidos de la misma serie y periodo se suman. Los periodos
    sin registro se rellenan con 0 (``fill="zero"``) o se dejan en ``NaN``
    (``fill="nan"``); en ambos casos se informan en ``Panel.filled_cells``.

    Si ``origin`` es ``None`` se toma de la columna ``origin`` cuando existe y tiene
    un único valor; si no, se asume transaccional.
    """
    if fill not in ("zero", "nan"):
        raise ValueError(f"fill debe ser 'zero' o 'nan', no {fill!r}.")
    if origin is None:
        origin = _infer_origin(df)

    data = df[[date_col, series_col, value_col]].copy()
    data[date_col] = pd.to_datetime(data[date_col])
    wide = data.pivot_table(
        index=date_col, columns=series_col, values=value_col, aggfunc="sum"
    ).sort_index()
    full_idx = pd.date_range(wide.index.min(), wide.index.max(), freq=freq)
    wide = wide.reindex(full_idx)
    filled = int(wide.isna().to_numpy().sum())
    if fill == "zero":
        wide = wide.fillna(0)

    return Panel(
        values=wide.to_numpy(dtype=np.float64),
        index=pd.DatetimeIndex(wide.index),
        series_ids=tuple(str(c) for c in wide.columns),
        origin=origin,
        freq=freq,
        filled_cells=filled,
    )


def _infer_origin(df: pd.DataFrame) -> DataOrigin:
    if "origin" in df.columns:
        values = df["origin"].dropna().unique()
        if len(values) == 1:
            return DataOrigin(str(values[0]))
        if len(values) > 1:
            raise ValueError(f"El conjunto mezcla orígenes de datos: {sorted(map(str, values))}.")
    return DataOrigin.TRANSACCIONAL
