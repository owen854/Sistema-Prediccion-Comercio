"""Figuras reproducibles de los patrones de consumo (RF-23, RNF-28).

Cada función recibe datos ya calculados y guarda un PNG; no calcula nada propio,
para que las cifras salgan siempre de los módulos de análisis.
"""

from __future__ import annotations

from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.dates as mdates
import matplotlib.pyplot as plt
import pandas as pd
from matplotlib.figure import Figure

from forecast_core.eda.decomposition import Decomposition

MONTHS_ES = ["Ene", "Feb", "Mar", "Abr", "May", "Jun", "Jul", "Ago", "Sep", "Oct", "Nov", "Dic"]
COLOR = "#B45309"
COLOR_2 = "#0F766E"


def _save(fig: Figure, path: Path) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    fig.tight_layout()
    fig.savefig(path, dpi=150)
    plt.close(fig)
    return path


def plot_index_and_trend(dec: Decomposition, path: Path, title: str) -> Path:
    fig, ax = plt.subplots(figsize=(10, 4))
    ax.plot(dec.observed.index, dec.observed, color=COLOR, lw=1, label="Índice de ventas reales")
    ax.plot(dec.trend.index, dec.trend, color=COLOR_2, lw=2, label="Tendencia (media móvil 2×12)")
    ax.set_title(title)
    ax.set_ylabel("Índice (2019 = 100)")
    ax.legend(frameon=False)
    ax.grid(alpha=0.3)
    return _save(fig, path)


def plot_seasonal_effects(dec: Decomposition, path: Path) -> Path:
    effects = dec.seasonal_effect_pct
    fig, ax = plt.subplots(figsize=(9, 3.8))
    colors = [COLOR if v >= 0 else COLOR_2 for v in effects]
    ax.bar(MONTHS_ES[: len(effects)], effects.to_numpy(), color=colors)
    for i, v in enumerate(effects):
        ax.annotate(
            f"{v:+.1f} %", (i, v), ha="center", va="bottom" if v >= 0 else "top", fontsize=8
        )
    ax.axhline(0, color="black", lw=0.8)
    ax.set_title("Efecto estacional de cada mes sobre las ventas reales")
    ax.set_ylabel("% frente a un mes promedio")
    return _save(fig, path)


def plot_inflation(local: pd.Series, national: pd.Series, path: Path, *, sintetico: bool) -> Path:
    """Inflación anual de Cúcuta frente a la nacional; marca de agua si los datos son sintéticos."""
    fig, ax = plt.subplots(figsize=(10, 4))
    ax.plot(local.index, local, color=COLOR, lw=1.5, label="Cúcuta")
    ax.plot(national.index, national, color=COLOR_2, lw=1.5, label="Nacional")
    ax.set_title("Inflación anual de Cúcuta frente a la nacional")
    ax.set_ylabel("Variación anual del IPC (%)")
    ax.legend(frameon=False)
    ax.grid(alpha=0.3)
    if sintetico:
        ax.text(
            0.5,
            0.5,
            "DATOS SINTÉTICOS\nno es evidencia",
            transform=ax.transAxes,
            ha="center",
            va="center",
            fontsize=28,
            color="#B91C1C",
            alpha=0.25,
            rotation=15,
        )
    return _save(fig, path)


def plot_border_flows(entries: pd.Series, events: pd.DataFrame, path: Path) -> Path:
    fig, ax = plt.subplots(figsize=(10, 4))
    ax.plot(entries.index, entries / 1000, color=COLOR_2, lw=1.2)
    for inicio, regimen, ev_id in zip(
        pd.DatetimeIndex(events["inicio"]),
        events["regimen"].astype(str),
        events["id"].astype(str),
        strict=True,
    ):
        x = float(mdates.date2num(inicio))  # type: ignore[no-untyped-call]
        style = "--" if regimen == "cerrada" else ":"
        ax.axvline(x, color="#B91C1C" if regimen == "cerrada" else "#15803D", ls=style)
        ax.annotate(
            ev_id.replace("_", " "),
            (x, ax.get_ylim()[1]),
            rotation=90,
            va="top",
            ha="right",
            fontsize=7,
        )
    ax.set_title("Entradas de extranjeros por los puestos de Norte de Santander")
    ax.set_ylabel("Miles de entradas por mes")
    ax.grid(alpha=0.3)
    return _save(fig, path)


def plot_cross_correlation(ccf: pd.DataFrame, band: float, path: Path, title: str) -> Path:
    fig, ax = plt.subplots(figsize=(9, 3.8))
    ax.bar(ccf["rezago"], ccf["correlacion"], color=COLOR_2, width=0.6)
    ax.axhspan(
        -band, band, color="grey", alpha=0.2, label=f"±1,96/√n = ±{band:.3f}".replace(".", ",")
    )
    ax.axhline(0, color="black", lw=0.8)
    ax.set_xlabel("Rezago k (meses): flujos en t−k frente a ventas en t")
    ax.set_ylabel("Correlación")
    ax.set_title(title)
    ax.legend(frameon=False)
    return _save(fig, path)
