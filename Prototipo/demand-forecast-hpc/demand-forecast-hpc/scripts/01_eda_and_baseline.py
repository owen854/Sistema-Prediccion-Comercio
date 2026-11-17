"""ETAPA 1 - Comprensión de los datos + línea base + marco de evaluación.

Ejecutar desde la carpeta raíz del proyecto:
    python scripts/01_eda_and_baseline.py

Con ventas reales de un comercio:
    python scripts/01_eda_and_baseline.py --sales data/ventas.csv --exog data/exogenas.csv

Si existe data/trm_real.csv (ver scripts/00_download_real_data.py) se usa la TRM real.
Por defecto los datos llegan hasta AYER (último día completo) y se pronostican los
siguientes 14 días.
"""
import argparse
import datetime as dt
import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from src import data_generation, data_loader               # noqa: E402
from src.baselines import seasonal_naive                    # noqa: E402
from src.metrics import rmse, mape, n_zero_excluded         # noqa: E402
from src.validation import rolling_origin_folds             # noqa: E402

HORIZON = 14      # días a pronosticar
N_FOLDS = 6       # orígenes móviles
SEED = 42


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--sales")
    ap.add_argument("--exog")
    ap.add_argument("--n-series", type=int, default=60)
    ap.add_argument("--start", default="2023-01-01")
    ap.add_argument("--end", default=str(dt.date.today() - dt.timedelta(days=1)),
                    help="último día con datos (por defecto, ayer)")
    args = ap.parse_args()

    (ROOT / "data").mkdir(exist_ok=True)
    (ROOT / "results").mkdir(exist_ok=True)

    # ------------------------------------------------------------ datos
    if args.sales and args.exog:
        sales, exog = data_loader.load_csv(args.sales, args.exog)
        origen = "REAL"
    else:
        trm_path = ROOT / "data" / "trm_real.csv"
        trm_real = None
        if trm_path.exists():
            t = pd.read_csv(trm_path, parse_dates=["date"]).set_index("date")["trm_cop_usd"]
            trm_real = t
        sales, exog = data_generation.generate(n_series=args.n_series, start=args.start,
                                               end=args.end, seed=SEED, trm_real=trm_real)
        sales.to_csv(ROOT / "data" / "synthetic_sales.csv", index=False)
        exog.to_csv(ROOT / "data" / "synthetic_exog.csv", index=False)
        origen = "SINTETICO (ventas) + TRM REAL" if trm_real is not None else "SINTETICO (ventas y TRM)"
    print(f"\n=== Origen de los datos: {origen} ===")

    report = data_loader.quality_report(sales)
    print("\n--- Reporte de calidad (Fase 1, CRISP-DM) ---")
    for k, v in report.items():
        print(f"  {k:>16}: {v}")

    Y, dates, ids = data_loader.to_matrix(sales)
    T, N = Y.shape
    print(f"\nMatriz de ventas: {T} días x {N} series")

    # ------------------------------------------------------------ EDA
    total = pd.Series(Y.sum(axis=1), index=dates)
    ex = exog.set_index("date").reindex(dates)
    dow = total.groupby(total.index.dayofweek).mean()
    dow = dow / dow.mean()
    closed = ex["border_closed"].fillna(0).astype(bool)
    eff_cierre = total[closed].mean() / total[~closed].mean() - 1 if closed.any() else float("nan")
    corr = np.corrcoef(total.values, ex["border_crossings"].fillna(ex["border_crossings"].mean()).values)[0, 1]

    print("\n--- Hallazgos exploratorios ---")
    print("  Índice por día de la semana (1.00 = promedio; 0=lunes):")
    print("   ", {int(k): round(float(v), 2) for k, v in dow.items()})
    print(f"  Días con cierre fronterizo: {int(closed.sum())}")
    print(f"  Ventas en días de cierre vs. normales: {eff_cierre:+.1%}")
    print(f"  Correlación ventas totales vs. aforo fronterizo: {corr:.2f}")

    fig, ax = plt.subplots(2, 1, figsize=(11, 6), sharex=True)
    ax[0].plot(total.index, total.values, lw=0.8)
    ax[0].set_ylabel("Unidades/día (total)")
    ax[0].set_title(f"Ventas agregadas ({origen}) y cierres fronterizos")
    for d in total.index[closed.values]:
        ax[0].axvline(d, color="red", alpha=0.15)
    ax[1].plot(ex.index, ex["border_crossings"], lw=0.8, color="tab:green")
    ax[1].set_ylabel("Cruces fronterizos/día")
    fig.tight_layout()
    fig.savefig(ROOT / "results" / "eda_series.png", dpi=130)
    plt.close(fig)

    # ------------------------------------------------------------ línea base + validación
    print(f"\n--- Línea base: ingenuo estacional (m=7), horizonte={HORIZON} d, "
          f"{N_FOLDS} orígenes móviles ---")
    rows = []
    for f in rolling_origin_folds(T, HORIZON, N_FOLDS):
        train = Y[:f.train_end]
        test = Y[f.train_end:f.test_end]
        pred = seasonal_naive(train, HORIZON, season=7)
        rows.append({
            "fold": f.index,
            "train_end": str(dates[f.train_end - 1].date()),
            "test": f"{dates[f.train_end].date()}..{dates[f.test_end - 1].date()}",
            "RMSE": rmse(test, pred),
            "MAPE_%": mape(test, pred),
            "ceros_excluidos": n_zero_excluded(test),
        })
    res = pd.DataFrame(rows)
    print(res.round(2).to_string(index=False))
    print(f"\n  PROMEDIO  RMSE={res['RMSE'].mean():.2f}   MAPE={res['MAPE_%'].mean():.2f}%")

    res.to_csv(ROOT / "results" / "baseline_seasonal_naive.csv", index=False)

    # ------------------------------------------------------------ pronóstico a FUTURO
    # Se entrena con TODOS los datos y se predicen los HORIZON días posteriores al último dato.
    last_day = dates[-1]
    fut_dates = pd.date_range(last_day + pd.Timedelta(days=1), periods=HORIZON, freq="D")
    fut = seasonal_naive(Y, HORIZON, season=7)
    fut_df = pd.DataFrame(fut, index=fut_dates, columns=ids).rename_axis("date")
    fut_df.to_csv(ROOT / "results" / "forecast_future_seasonal_naive.csv")
    print(f"\n--- Pronóstico a futuro (ingenuo estacional) ---")
    print(f"  Último dato real: {last_day.date()}")
    print(f"  Pronóstico: {fut_dates[0].date()} .. {fut_dates[-1].date()}  (total de unidades/día, todas las series)")
    print("   ", {str(d.date()): int(v) for d, v in fut_df.sum(axis=1).items()})
    with open(ROOT / "results" / "data_quality.json", "w", encoding="utf-8") as fh:
        json.dump({"origen": origen, **report}, fh, ensure_ascii=False, indent=2)
    print("\nArchivos en results/: eda_series.png, baseline_seasonal_naive.csv, data_quality.json")


if __name__ == "__main__":
    main()
