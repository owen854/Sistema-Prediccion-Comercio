"""Comparación de la inflación anual local con la nacional (RF-20; Patrón 3 del informe)."""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np
import pandas as pd


def annual_inflation(index: pd.Series, periods: int = 12) -> pd.Series:
    """Inflación anual en %: (I_t / I_{t−12} − 1) · 100."""
    return ((index / index.shift(periods) - 1.0) * 100.0).dropna()


@dataclass(frozen=True)
class InflationGap:
    brecha_media: float  # puntos porcentuales (local − nacional)
    meses_por_encima: int
    meses_totales: int
    brecha_maxima: float
    fecha_brecha_maxima: pd.Timestamp
    pico_local: float
    fecha_pico_local: pd.Timestamp
    pico_nacional: float
    fecha_pico_nacional: pd.Timestamp


def inflation_gap(local_index: pd.Series, national_index: pd.Series) -> InflationGap:
    """Brecha entre la inflación anual local y la nacional en los meses comunes."""
    local = annual_inflation(local_index)
    national = annual_inflation(national_index)
    common = local.index.intersection(national.index)
    if common.empty:
        raise ValueError("Las series no tienen meses en común.")
    gap = local[common] - national[common]
    return InflationGap(
        brecha_media=float(gap.mean()),
        meses_por_encima=int((gap > 0).sum()),
        meses_totales=len(gap),
        brecha_maxima=float(gap.max()),
        fecha_brecha_maxima=_date_of_max(gap),
        pico_local=float(local[common].max()),
        fecha_pico_local=_date_of_max(local[common]),
        pico_nacional=float(national[common].max()),
        fecha_pico_nacional=_date_of_max(national[common]),
    )


def _date_of_max(series: pd.Series) -> pd.Timestamp:
    return pd.DatetimeIndex(series.index)[int(np.argmax(series.to_numpy()))]


def cumulative_change(index: pd.Series, start: str, end: str) -> float:
    """Variación acumulada en % entre dos meses (``"AAAA-MM"``)."""
    a = index[pd.Timestamp(f"{start}-01")]
    b = index[pd.Timestamp(f"{end}-01")]
    return float((b / a - 1.0) * 100.0)
