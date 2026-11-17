#!/usr/bin/env bash
# Prepara WSL2 Ubuntu para el backend y el cómputo paralelo (Documentacion Tecnica/05).
# Uso (desde Ubuntu):
#   bash "/mnt/c/Users/PC/Documents/GitHub/Sistema-Prediccion-Comercio/Codigo Fuente/scripts/setup_wsl_hpc.sh"
# Pide la contraseña de Ubuntu una vez (apt y PostgreSQL).
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
VENV="$HOME/.venvs/prediccion-demanda"

paso() { printf '\n\033[1;33m== %s\033[0m\n' "$1"; }

paso "1/6 Paquetes del sistema: CMake, Ninja, encabezados de Python, OpenMPI, PostgreSQL"
sudo apt-get update
sudo apt-get install -y build-essential cmake ninja-build pkg-config \
  python3-dev python3-venv openmpi-bin libopenmpi-dev postgresql

paso "2/6 uv (gestor de entornos de Python)"
if ! command -v uv >/dev/null 2>&1; then
  curl -LsSf https://astral.sh/uv/install.sh | sh
fi
export PATH="$HOME/.local/bin:$PATH"
uv --version

paso "3/6 Entorno del proyecto en $VENV (fuera de /mnt/c, por rendimiento)"
export UV_PROJECT_ENVIRONMENT="$VENV"
if ! grep -q "UV_PROJECT_ENVIRONMENT" "$HOME/.bashrc"; then
  echo "export UV_PROJECT_ENVIRONMENT=\"$VENV\"" >> "$HOME/.bashrc"
fi
cd "$ROOT/backend"
uv sync --extra hpc --extra kernels

paso "4/6 PostgreSQL de desarrollo (usuario y base 'forecast')"
sudo service postgresql start
sudo -u postgres psql -tc "SELECT 1 FROM pg_roles WHERE rolname='forecast'" | grep -q 1 \
  || sudo -u postgres psql -c "CREATE ROLE forecast LOGIN PASSWORD 'forecast';"
sudo -u postgres psql -tc "SELECT 1 FROM pg_database WHERE datname='forecast'" | grep -q 1 \
  || sudo -u postgres createdb -O forecast forecast
uv run alembic upgrade head

paso "5/6 Verificación de OpenMP, MPI y pruebas"
cmake --version | head -1
mpiexec --version | head -1
uv run python -c "import forecast_hpc_kernels as k; print('Núcleos OpenMP compilados; hilos máximos:', k.max_threads())"
uv run python -c "from mpi4py import MPI; print('mpi4py:', MPI.Get_library_version().splitlines()[0])"
uv run pytest -q -m "not cuda" -p no:warnings

paso "6/6 Prueba de los núcleos en C++ puro"
cmake -S "$ROOT/hpc_kernels" -B /tmp/hpc_kernels_build -G Ninja \
  -DHPC_KERNELS_BUILD_TESTS=ON -DCMAKE_BUILD_TYPE=Release >/dev/null
cmake --build /tmp/hpc_kernels_build >/dev/null
/tmp/hpc_kernels_build/test_features

paso "Listo. Abra una terminal nueva para que se apliquen las variables de entorno."
