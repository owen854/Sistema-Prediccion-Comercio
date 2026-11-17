"""Benchmarks de cómputo paralelo (RF-40). *Spike* de la Fase 0, base de la Fase 3.

Subcomandos::

    # OpenMP: media móvil sobre un panel sintético con 1, 2, 4 y 8 hilos
    python -m forecast_core.pipelines.benchmark omp --series 500 --days 1460

    # MPI: validación con origen móvil repartida entre procesos (una corrida por p)
    mpiexec -n 4 python -m forecast_core.pipelines.benchmark mpi --folds 24

    # Resumen: aceleración, eficiencia y ajuste de Amdahl de las corridas MPI
    python -m forecast_core.pipelines.benchmark resumen

Los resultados se guardan en ``experiments/results/spike/`` con la descripción del
hardware. Los datos son SINTÉTICOS: sirven para medir rendimiento, no para concluir
nada sobre la demanda real.
"""

from __future__ import annotations

import argparse
import functools
import json
import sys
import time
from collections.abc import Sequence
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

import numpy as np

from forecast_core.config import project_root
from forecast_core.evaluation.backtesting import Fold, rolling_origin_folds
from forecast_core.evaluation.metrics import mape, rmse
from forecast_core.features.rolling import rolling_mean as rolling_mean_ref
from forecast_core.hpc import benchmark as bm
from forecast_core.hpc import mpi, omp
from forecast_core.ingestion import synthetic
from forecast_core.models.naive import seasonal_naive
from forecast_core.preprocessing.panel import to_panel
from forecast_core.types import Panel

RESULTS_DIR = Path("experiments") / "results" / "spike"
WINDOWS = (7, 14, 28, 56)


def synthetic_panel(n_series: int, days: int, seed: int) -> Panel:
    end = (np.datetime64("2023-01-01") + np.timedelta64(days - 1, "D")).astype(str)
    sales, _ = synthetic.generate(n_series=n_series, start="2023-01-01", end=end, seed=seed)
    return to_panel(sales)


def _save(name: str, payload: dict[str, Any]) -> Path:
    out_dir = project_root() / RESULTS_DIR
    out_dir.mkdir(parents=True, exist_ok=True)
    stamp = datetime.now(UTC).strftime("%Y%m%dT%H%M%S")
    path = out_dir / f"{name}_{stamp}.json"
    path.write_text(json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8")
    return path


# --------------------------------------------------------------------------- OpenMP
def run_omp(args: argparse.Namespace) -> dict[str, Any]:
    panel = synthetic_panel(args.series, args.days, args.seed)
    values = panel.values
    reference = rolling_mean_ref(values, args.window)
    t_ref = bm.time_call(lambda: rolling_mean_ref(values, args.window), args.repeats)

    result: dict[str, Any] = {
        "experimento": "omp_rolling_mean",
        "origen_datos": panel.origin.value,
        "forma": [panel.n_periods, panel.n_series],
        "ventana": args.window,
        "referencia_numpy_s": t_ref.as_dict(),
        "hardware": bm.hardware_info(),
        "corridas": [],
    }
    if not omp.KERNELS_AVAILABLE:
        result["aviso"] = "forecast_hpc_kernels no está instalado: solo se midió la referencia."
        return result

    t1: float | None = None
    for h in args.threads:
        out = omp.rolling_mean(values, args.window, threads=h, backend="openmp")
        equal = bool(np.allclose(out, reference, rtol=1e-9, atol=1e-9, equal_nan=True))
        timing = bm.time_call(
            functools.partial(omp.rolling_mean, values, args.window, threads=h, backend="openmp"),
            args.repeats,
        )
        t1 = timing.median if h == 1 else t1
        row: dict[str, Any] = {"hilos": h, "tiempo_s": timing.as_dict(), "equivalente": equal}
        if t1 is not None:
            row["aceleracion"] = bm.speedup(t1, timing.median)
            row["eficiencia"] = bm.efficiency(t1, timing.median, h)
        result["corridas"].append(row)
    return result


# --------------------------------------------------------------------------- MPI
def backtest_fold(values: np.ndarray, fold: Fold, season: int = 7) -> dict[str, float]:
    """Tarea independiente: variables de la ventana de entrenamiento + línea base + métricas."""
    train = values[: fold.train_end]
    test = values[fold.train_end : fold.test_end]
    features = [rolling_mean_ref(train, w)[-1] for w in WINDOWS]
    pred = seasonal_naive(train, fold.horizon, season)
    return {
        "fold": fold.index,
        "rmse": rmse(test, pred),
        "mape": mape(test, pred),
        "media_variables": float(np.nanmean(np.stack(features))),
    }


def run_mpi(args: argparse.Namespace) -> dict[str, Any] | None:
    comm = mpi.get_comm()
    rank, size = mpi.rank_and_size(comm)

    values: np.ndarray | None = None
    if rank == 0:
        values = synthetic_panel(args.series, args.days, args.seed).values
    if comm is not None:
        comm.Barrier()
    t0 = time.perf_counter()
    if comm is not None and size > 1:
        values = comm.bcast(values, root=0)  # comunicación: el panel viaja a cada proceso
    if values is None:
        raise RuntimeError("El panel no llegó a este proceso.")
    folds = list(rolling_origin_folds(values.shape[0], args.horizon, args.folds, step=args.step))
    results = mpi.mpi_map(lambda f: backtest_fold(values, f), folds, comm)
    if comm is not None:
        comm.Barrier()
    elapsed = time.perf_counter() - t0
    if rank != 0 or results is None:
        return None

    payload: dict[str, Any] = {
        "experimento": "mpi_backtest",
        "origen_datos": "sintetico",
        "procesos": size,
        "forma": list(values.shape),
        "particiones": len(folds),
        "tiempo_s": elapsed,
        "rmse_medio": float(np.mean([r["rmse"] for r in results])),
        "hardware": bm.hardware_info(),
    }
    if args.verificar:
        sequential = [backtest_fold(values, f) for f in folds]
        payload["equivalente_a_secuencial"] = sequential == results
    return payload


# --------------------------------------------------------------------------- resumen
def run_summary(_: argparse.Namespace) -> dict[str, Any]:
    files = sorted((project_root() / RESULTS_DIR).glob("mpi_backtest_*.json"))
    runs = [json.loads(f.read_text(encoding="utf-8")) for f in files]
    if not runs:
        raise SystemExit("No hay corridas MPI guardadas en experiments/results/spike/.")
    by_p: dict[int, list[float]] = {}
    for r in runs:
        by_p.setdefault(int(r["procesos"]), []).append(float(r["tiempo_s"]))
    if 1 not in by_p:
        raise SystemExit("Falta la corrida con 1 proceso (T1).")
    t1 = float(np.median(by_p[1]))
    tabla = []
    for p in sorted(by_p):
        tp = float(np.median(by_p[p]))
        tabla.append(
            {
                "procesos": p,
                "corridas": len(by_p[p]),
                "tiempo_mediana_s": tp,
                "aceleracion": bm.speedup(t1, tp),
                "eficiencia": bm.efficiency(t1, tp, p),
            }
        )
    ps = [row["procesos"] for row in tabla]
    ss = [row["aceleracion"] for row in tabla]
    f = bm.fit_amdahl(ps, ss) if any(p > 1 for p in ps) else None
    return {"tabla": tabla, "fraccion_paralelizable_f": f}


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    sub = parser.add_subparsers(dest="cmd", required=True)

    p_omp = sub.add_parser("omp", help="Media móvil con núcleos OpenMP")
    p_omp.add_argument("--series", type=int, default=500)
    p_omp.add_argument("--days", type=int, default=1460)
    p_omp.add_argument("--window", type=int, default=28)
    p_omp.add_argument("--threads", type=int, nargs="+", default=[1, 2, 4, 8])
    p_omp.add_argument("--repeats", type=int, default=5)
    p_omp.add_argument("--seed", type=int, default=42)

    p_mpi = sub.add_parser("mpi", help="Origen móvil repartido con MPI")
    p_mpi.add_argument("--series", type=int, default=500)
    p_mpi.add_argument("--days", type=int, default=1460)
    p_mpi.add_argument("--folds", type=int, default=24)
    p_mpi.add_argument("--horizon", type=int, default=14)
    p_mpi.add_argument("--step", type=int, default=7)
    p_mpi.add_argument("--seed", type=int, default=42)
    p_mpi.add_argument("--no-verificar", dest="verificar", action="store_false")

    sub.add_parser("resumen", help="Aceleración y eficiencia de las corridas MPI")
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    if args.cmd == "omp":
        payload: dict[str, Any] | None = run_omp(args)
        name = "omp_rolling_mean"
    elif args.cmd == "mpi":
        payload = run_mpi(args)
        name = "mpi_backtest"
    else:
        print(json.dumps(run_summary(args), indent=2, ensure_ascii=False))
        return 0
    if payload is not None:
        path = _save(name, payload)
        print(json.dumps({k: v for k, v in payload.items() if k != "hardware"}, indent=2))
        print(f"Resultado guardado en {path}", file=sys.stderr)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
