#!/usr/bin/env bash
# Corre el benchmark MPI con 1, 2 y 4 procesos (y 8 con sobresuscripción) y muestra el resumen.
# Uso (WSL, desde cualquier carpeta):  bash scripts/run_benchmark_mpi.sh [repeticiones] [series]
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
REPS="${1:-5}"
SERIES="${2:-500}"
cd "$ROOT/backend"

for p in 1 2 4 8; do
  extra=()
  [ "$p" -gt 4 ] && extra=(--oversubscribe)
  for _ in $(seq "$REPS"); do
    echo "== p=$p"
    mpiexec -n "$p" "${extra[@]}" uv run --no-sync python -m forecast_core.pipelines.benchmark \
      mpi --series "$SERIES" > /dev/null
  done
done

uv run --no-sync python -m forecast_core.pipelines.benchmark resumen
