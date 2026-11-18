"""Reproduce desde el código la evidencia del OE1 (HU-08; RF-18 a RF-21, RF-23; RNF-28).

Uso::

    python -m forecast_core.pipelines.reproduce_oe1

Calcula los patrones de consumo del Informe de evidencia OE1/OE2 a partir de los
archivos originales, los compara con las cifras publicadas y guarda tablas y figuras
en ``experiments/results/oe1/``. Termina con código 1 si alguna cifra difiere más que
la tolerancia (una unidad del último decimal publicado).
"""

from __future__ import annotations

import json
import sys
from collections.abc import Sequence
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import pandas as pd

from forecast_core.config import load_yaml, resolve_path
from forecast_core.eda import cross_correlation as cc
from forecast_core.eda import decomposition, growth, inflation, report
from forecast_core.ingestion import calendar
from forecast_core.pipelines.ingest import SOURCES_CONFIG, build_panel, load_sources

OUT_DIR = Path("experiments") / "results" / "oe1"
PANDEMIA = [("2020-03", "2022-02")]


@dataclass(frozen=True)
class Check:
    patron: str
    indicador: str
    informe: float
    obtenido: float | None
    decimales: int
    sintetico: bool = False  # calculado con datos sintéticos: nunca se compara con el informe

    @property
    def estado(self) -> str:
        if self.obtenido is None:
            return "pendiente"
        if self.sintetico:
            return "sintético (no comparable)"
        tol = 10 ** (-self.decimales) + 1e-9
        return "coincide" if abs(round(self.obtenido, 6) - self.informe) <= tol else "difiere"

    def as_row(self) -> dict[str, Any]:
        obt = None if self.obtenido is None else round(self.obtenido, self.decimales + 2)
        return {
            "patron": self.patron,
            "indicador": self.indicador,
            "informe": self.informe,
            "obtenido": obt,
            "estado": self.estado,
        }


def run() -> tuple[list[Check], dict[str, Path]]:
    cfg = load_yaml(SOURCES_CONFIG)
    series = load_sources(cfg, permitir_sintetico=True)
    emc = series["emc_ventas_reales"]
    ent = series["entradas_norte_de_santander"]
    out = resolve_path(OUT_DIR)
    figs: dict[str, Path] = {}

    # Tabla IV: calidad y alineación
    panel_lstm = build_panel({"emc": emc, "entradas": ent})
    checks = [
        Check("Tabla IV", "Meses de la EMC", 164, len(emc), 0),
        Check("Tabla IV", "Meses de entradas por Norte de Santander", 174, len(ent), 0),
        Check("Tabla IV", "Meses del panel para la LSTM", 162, len(panel_lstm), 0),
        Check("Tabla IV", "Entradas totales por los 5 puestos", 3_411_542, float(ent.sum()), 0),
    ]

    # Patrón 1: tendencia y choque
    means = growth.annual_means(emc)
    shock = growth.deepest_shock(emc)
    checks += [
        Check("Patrón 1", "Índice promedio 2013", 78.5, float(means[2013]), 1),
        Check("Patrón 1", "Índice promedio 2025", 128.3, float(means[2025]), 1),
        Check(
            "Patrón 1",
            "Crecimiento real anual 2013-2025 (%)",
            4.2,
            100 * growth.average_annual_growth(emc, 2013, 2025),
            1,
        ),
        Check("Patrón 1", "Mínimo (abril 2020)", 55.5, shock.valor, 1),
        Check(
            "Patrón 1",
            "Caída abr-2020 frente a abr-2019 (%)",
            -39.0,
            100 * shock.variacion_anual,
            1,
        ),
    ]

    # Patrón 2: estacionalidad
    dec = decomposition.classical_multiplicative(emc)
    eff = dec.seasonal_effect_pct
    checks += [
        Check(
            "Patrón 2", "Fuerza de la estacionalidad", 0.76, decomposition.seasonal_strength(dec), 2
        ),
        Check("Patrón 2", "Efecto diciembre (%)", 28.8, float(eff[12]), 1),
        Check("Patrón 2", "Efecto noviembre (%)", 4.9, float(eff[11]), 1),
        Check("Patrón 2", "Efecto abril (%)", -9.9, float(eff[4]), 1),
        Check("Patrón 2", "Efecto febrero (%)", -7.7, float(eff[2]), 1),
    ]
    figs["fig1"] = report.plot_index_and_trend(
        dec,
        out / "fig1_indice_ventas_tendencia.png",
        "Índice de ventas reales del comercio minorista (total nacional)",
    )
    figs["fig2"] = report.plot_seasonal_effects(dec, out / "fig2_efecto_estacional.png")

    # Patrón 3: inflación de Cúcuta (requiere la historia del IPC por ciudades)
    if "ipc_cucuta" in series and "ipc_nacional" in series:
        cucuta, nacional = series["ipc_cucuta"], series["ipc_nacional"]
        sint = cucuta.attrs.get("origin") == "sintetico"
        gap = inflation.inflation_gap(cucuta, nacional)
        checks += [
            Check("Patrón 3", "Brecha media de inflación (pp)", 0.72, gap.brecha_media, 2, sint),
            Check("Patrón 3", "Meses con Cúcuta por encima", 64, gap.meses_por_encima, 0, sint),
            Check("Patrón 3", "Brecha máxima (pp)", 3.98, gap.brecha_maxima, 2, sint),
        ]
        figs["fig3"] = report.plot_inflation(
            inflation.annual_inflation(cucuta),
            inflation.annual_inflation(nacional),
            out / "fig3_inflacion_cucuta_nacional.png",
            sintetico=sint,
        )
    else:
        checks += [
            Check("Patrón 3", "Brecha media de inflación (pp)", 0.72, None, 2),
            Check("Patrón 3", "Meses con Cúcuta por encima", 64, None, 0),
            Check("Patrón 3", "Brecha máxima (pp)", 3.98, None, 2),
        ]

    # Patrón 4: flujos fronterizos
    caida_2015 = ent["2015-09-01":"2016-07-01"].sum() / ent["2014-09-01":"2015-07-01"].sum() - 1
    pandemia = ent["2020-04-01":"2021-05-01"]
    previo = ent["2019-04-01":"2020-03-01"]
    x, y = cc.yoy_change(ent), cc.yoy_change(emc)
    ccf_full = cc.cross_correlation(x, y)
    ccf_ex = cc.cross_correlation(cc.exclude_periods(x, PANDEMIA), cc.exclude_periods(y, PANDEMIA))
    best = cc.strongest_lag(ccf_ex)
    band = cc.significance_band(int(best["n"]))
    checks += [
        Check("Patrón 4", "Caída de entradas sep-2015 a jul-2016 (%)", -44.0, 100 * caida_2015, 1),
        Check(
            "Patrón 4",
            "Caída en la pandemia (%)",
            -99.8,
            100 * (pandemia.mean() / previo.mean() - 1),
            1,
        ),
        Check("Patrón 4", "Entradas por mes en la pandemia", 86, float(pandemia.mean()), 0),
        Check("Patrón 4", "Máximo mensual de entradas (feb-2018)", 89_381, float(ent.max()), 0),
        Check(
            "Patrón 4", "Promedio mensual de entradas 2025", 20_525, float(ent["2025"].mean()), 0
        ),
        Check(
            "Patrón 4",
            "Correlación máxima, serie completa",
            0.63,
            float(ccf_full["correlacion"].max()),
            2,
        ),
        Check("Patrón 4", "Correlación máxima sin pandemia", 0.28, float(best["correlacion"]), 2),
        Check("Patrón 4", "Rezago de la correlación máxima (meses)", 1, float(best["rezago"]), 0),
        Check("Patrón 4", "Banda de significancia (±)", 0.17, band, 2),
    ]
    events = calendar.border_events(calendar.load_calendar_config())
    figs["fig4"] = report.plot_border_flows(ent, events, out / "fig4_entradas_frontera.png")
    figs["fig5"] = report.plot_cross_correlation(
        ccf_ex,
        band,
        out / "fig5_correlacion_cruzada.png",
        "Correlación cruzada de variaciones anuales (sin mar-2020 a feb-2022)",
    )

    out.mkdir(parents=True, exist_ok=True)
    table = pd.DataFrame([c.as_row() for c in checks])
    table.to_csv(out / "comparacion_informe.csv", index=False, encoding="utf-8")
    ccf_ex.to_csv(out / "correlacion_cruzada_sin_pandemia.csv", index=False)
    dec.seasonal_effect_pct.rename("efecto_pct").to_csv(out / "efectos_estacionales.csv")
    summary = table["estado"].value_counts().to_dict()
    (out / "resumen.json").write_text(
        json.dumps(
            {"estados": summary, "figuras": {k: v.name for k, v in figs.items()}},
            indent=2,
            ensure_ascii=False,
        ),
        encoding="utf-8",
    )
    return checks, figs


def main(argv: Sequence[str] | None = None) -> int:
    checks, figs = run()
    table = pd.DataFrame([c.as_row() for c in checks])
    with pd.option_context("display.max_rows", 100, "display.width", 140):
        print(table.to_string(index=False))
    print(f"\nFiguras: {', '.join(p.name for p in figs.values())}")
    print(f"Resultados en {resolve_path(OUT_DIR)}", file=sys.stderr)
    return 1 if any(c.estado == "difiere" for c in checks) else 0


if __name__ == "__main__":
    raise SystemExit(main())
