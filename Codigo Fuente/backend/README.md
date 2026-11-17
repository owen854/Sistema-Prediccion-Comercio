# Backend (Python)

Contiene dos paquetes (ADR-008):

| Paquete | Qué es | Depende de |
|---|---|---|
| `forecast_core` | Núcleo analítico: ingesta, calidad, panel T×N, variables, modelos, evaluación, inventario y estrategias de paralelismo. | numpy, pandas (y extras opcionales) |
| `forecast_api` | API REST con FastAPI, base de datos y worker de trabajos. | `forecast_core` |

`forecast_core` **nunca** importa `forecast_api` (lo verifica `tests/unit/test_arquitectura.py`).

## Instalación

```bash
uv sync                         # entorno base + herramientas de desarrollo
uv sync --extra hpc --extra kernels   # en WSL/Linux: MPI y núcleos OpenMP
uv sync --extra stats --extra dl      # modelos (Fase 2)
```

## Comandos frecuentes

| Tarea | Comando |
|---|---|
| Pruebas rápidas | `uv run pytest -m "not mpi and not cuda"` |
| Cobertura | `uv run pytest --cov` |
| Estilo y errores | `uv run ruff check . && uv run ruff format --check .` |
| Tipos | `uv run mypy` |
| API en modo desarrollo | `uv run uvicorn forecast_api.main:app --reload` |
| Migraciones | `uv run alembic upgrade head` |
| Benchmark OpenMP | `uv run python -m forecast_core.pipelines.benchmark omp` |
| Benchmark MPI | `mpiexec -n 4 uv run --no-sync python -m forecast_core.pipelines.benchmark mpi` |
