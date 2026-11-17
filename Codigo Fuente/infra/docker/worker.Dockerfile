# Worker de trabajos con OpenMPI y núcleos OpenMP compilados (Fase 4).
# Para GPU, cambiar la imagen base por una de PyTorch con CUDA y agregar --extra dl.
FROM python:3.12-slim

RUN apt-get update \
 && apt-get install -y --no-install-recommends build-essential cmake openmpi-bin libopenmpi-dev \
 && rm -rf /var/lib/apt/lists/*

COPY --from=ghcr.io/astral-sh/uv:0.13.9 /uv /bin/uv
ENV UV_COMPILE_BYTECODE=1 UV_LINK_MODE=copy FORECAST_PROJECT_ROOT=/app \
    OMPI_ALLOW_RUN_AS_ROOT=1 OMPI_ALLOW_RUN_AS_ROOT_CONFIRM=1

WORKDIR /app
COPY configs ./configs
COPY hpc_kernels ./hpc_kernels
COPY backend ./backend

WORKDIR /app/backend
RUN uv sync --frozen --no-dev --extra hpc --extra kernels

CMD ["uv", "run", "--no-sync", "python", "-m", "forecast_api.worker.runner"]
