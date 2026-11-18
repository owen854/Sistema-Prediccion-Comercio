"""Crecimiento real y choques de una serie mensual (RF-19; Patrón 1 del informe)."""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np
import pandas as pd


def annual_means(series: pd.Series) -> pd.Series:
    """Promedio por año calendario."""
    return series.groupby(pd.DatetimeIndex(series.index).year).mean()


def average_annual_growth(series: pd.Series, start_year: int, end_year: int) -> float:
    """Crecimiento anual compuesto entre los promedios de dos años: (P_fin / P_ini)^(1/años) − 1."""
    means = annual_means(series)
    if start_year not in means.index or end_year not in means.index:
        raise ValueError(f"Faltan los años {start_year} o {end_year} en la serie.")
    years = end_year - start_year
    if years <= 0:
        raise ValueError("end_year debe ser mayor que start_year.")
    return float((means[end_year] / means[start_year]) ** (1 / years) - 1)


@dataclass(frozen=True)
class Shock:
    fecha: pd.Timestamp
    valor: float
    variacion_anual: float  # frente al mismo mes del año anterior


def deepest_shock(series: pd.Series, periods: int = 12) -> Shock:
    """Mínimo de la serie y su variación frente al mismo mes del año anterior."""
    fecha = pd.DatetimeIndex(series.index)[int(np.argmin(series.to_numpy()))]
    anterior = fecha - pd.DateOffset(months=periods)
    if anterior not in series.index:
        raise ValueError("No hay dato del mismo mes del año anterior al mínimo.")
    valor = float(series[fecha])
    return Shock(fecha=fecha, valor=valor, variacion_anual=valor / float(series[anterior]) - 1)
