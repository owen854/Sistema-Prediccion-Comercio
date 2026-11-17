# Atajos para Linux/WSL. En Windows use tasks.ps1.
# El entorno de Python de WSL vive en $UV_PROJECT_ENVIRONMENT (ver scripts/setup_wsl_hpc.sh).

BACKEND := backend
FRONTEND := frontend

.PHONY: setup-wsl test test-all lint typecheck api web kernels-test bench-omp bench-mpi gen-api migrate

setup-wsl:            ## Instala todo en WSL (pide contraseña para apt)
	bash scripts/setup_wsl_hpc.sh

test:                 ## Pruebas rápidas (sin MPI ni CUDA)
	cd $(BACKEND) && uv run pytest -q -m "not mpi and not cuda"

test-all:             ## Todas las pruebas que corren en esta máquina (incluye MPI y núcleos)
	cd $(BACKEND) && uv run pytest -q -m "not cuda" --cov
	cd $(FRONTEND) && npm test

lint:
	cd $(BACKEND) && uv run ruff format --check . && uv run ruff check .
	cd $(FRONTEND) && npm run lint

typecheck:
	cd $(BACKEND) && uv run mypy
	cd $(FRONTEND) && npm run typecheck

migrate:
	cd $(BACKEND) && uv run alembic upgrade head

api:
	cd $(BACKEND) && uv run uvicorn forecast_api.main:app --reload --host 0.0.0.0

web:
	cd $(FRONTEND) && npm run dev

kernels-test:         ## Prueba en C++ puro de los núcleos OpenMP
	cmake -S hpc_kernels -B /tmp/hpc_kernels_build -DHPC_KERNELS_BUILD_TESTS=ON -DCMAKE_BUILD_TYPE=Release
	cmake --build /tmp/hpc_kernels_build && /tmp/hpc_kernels_build/test_features

bench-omp:
	cd $(BACKEND) && uv run python -m forecast_core.pipelines.benchmark omp

bench-mpi:
	bash scripts/run_benchmark_mpi.sh

gen-api:              ## Regenera los tipos TypeScript desde la API en ejecución
	cd $(FRONTEND) && npm run gen:api
