# Código Fuente — Sistema de Predicción de Demanda

Sistema de predicción de demanda para MIPYMES del comercio minorista fronterizo de Norte de Santander, con machine learning y cómputo paralelo (OpenMP, MPI, CUDA).

| Documento | Contenido |
|---|---|
| [Requerimientos](../Documentacion%20Tecnica/01_Requerimientos_RF_RNF.md) | 66 RF y 29 RNF trazados a OE1–OE4 |
| [Arquitectura](../Documentacion%20Tecnica/03_Arquitectura_Sistema.md) | Componentes, PCAM, modelo de datos, API |
| [Plan de gestión](../Documentacion%20Tecnica/04_Plan_Gestion_Proyecto.md) | Fases, sprints, riesgos, Definición de Hecho |
| [Entorno y cómputo paralelo](../Documentacion%20Tecnica/05_Entorno_Desarrollo_HPC.md) | Windows + WSL2 + Colab, instalación de MPI y CMake |
| [Decisiones (ADR)](../Documentacion%20Tecnica/ADR/README.md) | Por qué se eligió cada tecnología |

## Estructura

| Carpeta | Contenido |
|---|---|
| `backend/` | Python: `forecast_core` (núcleo analítico) y `forecast_api` (FastAPI). Pruebas en `backend/tests/`. |
| `hpc_kernels/` | Núcleos C++ con OpenMP expuestos a Python con pybind11. |
| `frontend/` | Next.js: solo presentación; consume la API. |
| `configs/` | Configuración declarativa: fuentes, calendario, variables, inventario, paralelismo, experimentos. |
| `data/` | Datos (no versionados, salvo `manifest.json`). |
| `experiments/` | Resultados y registros de MLflow (no versionados). |
| `notebooks/` | Análisis reproducibles por objetivo específico. |
| `scripts/` | Instalación (Windows y WSL), benchmarks y respaldos. |
| `infra/` | Dockerfiles y cuaderno de Colab para CUDA. |

## Puesta en marcha

### Windows (frontend y backend en modo secuencial)

```powershell
powershell -ExecutionPolicy Bypass -File scripts\setup_dev.ps1
```

### WSL2 Ubuntu (backend completo, OpenMP, MPI y PostgreSQL)

```bash
bash scripts/setup_wsl_hpc.sh
```

### Ejecutar

| Qué | Windows | WSL / Linux |
|---|---|---|
| API (http://localhost:8000/docs) | `.\tasks.ps1 api` | `make api` |
| Web (http://localhost:3000) | `.\tasks.ps1 web` | `make web` |
| Pruebas | `.\tasks.ps1 test` | `make test-all` |
| Estilo y tipos | `.\tasks.ps1 lint` y `.\tasks.ps1 typecheck` | `make lint typecheck` |
| Benchmark OpenMP | — | `make bench-omp` |
| Benchmark MPI | — | `make bench-mpi` |
| CUDA | Cuaderno `infra/gpu_remota/run_cuda_experiments.ipynb` en Google Colab | |

Con Docker: `cp .env.example .env && docker compose up --build`.

## Reglas del proyecto

1. `forecast_core` nunca importa `forecast_api` (lo verifica una prueba).
2. Ninguna cifra sin origen: todo número que muestre la interfaz o el informe sale de una ejecución registrada.
3. Los datos sintéticos siempre se etiquetan como tales.
4. Los datos de comercios nunca se suben al repositorio (Ley 1581 de 2012).
5. Cada etapa paralela tiene una versión secuencial de referencia y una prueba de equivalencia.
