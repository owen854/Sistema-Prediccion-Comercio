# API FastAPI (núcleo en modo secuencial; sin MPI ni CUDA).
FROM python:3.12-slim

COPY --from=ghcr.io/astral-sh/uv:0.13.9 /uv /bin/uv
ENV UV_COMPILE_BYTECODE=1 UV_LINK_MODE=copy FORECAST_PROJECT_ROOT=/app

WORKDIR /app
COPY configs ./configs
COPY hpc_kernels ./hpc_kernels
COPY backend ./backend

WORKDIR /app/backend
RUN uv sync --frozen --no-dev

EXPOSE 8000
CMD ["sh", "-c", "uv run --no-sync alembic upgrade head && uv run --no-sync uvicorn forecast_api.main:app --host 0.0.0.0 --port 8000"]
