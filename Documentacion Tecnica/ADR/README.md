# Registro de Decisiones de Arquitectura (ADR)

Cada ADR documenta una decisión importante: su contexto, la decisión, las alternativas descartadas y sus consecuencias. Una decisión aceptada no se borra; si cambia, se crea un ADR nuevo que la reemplaza.

| ADR | Decisión | Estado |
|---|---|---|
| [ADR-001](ADR-001-stack-python-fastapi-nextjs.md) | Backend en Python con FastAPI y frontend en Next.js | Aceptada |
| [ADR-002](ADR-002-cola-trabajos-postgresql.md) | Cola de trabajos en PostgreSQL | Aceptada |
| [ADR-003](ADR-003-openmp-cpp-pybind11.md) | OpenMP con núcleos C++ expuestos con pybind11 | Aceptada |
| [ADR-004](ADR-004-mpi-mpi4py-openmpi.md) | MPI con mpi4py sobre OpenMPI | Aceptada |
| [ADR-005](ADR-005-cuda-pytorch-colab.md) | CUDA mediante PyTorch, ejecutado en Google Colab | Aceptada |
| [ADR-006](ADR-006-mlflow-seguimiento-experimentos.md) | MLflow local para el seguimiento de experimentos | Aceptada |
| [ADR-007](ADR-007-entorno-windows-wsl-colab.md) | Entorno híbrido Windows + WSL2 + Colab | Aceptada |
| [ADR-008](ADR-008-monorepo-uv-nucleo-independiente.md) | Monorepo en `Codigo Fuente/` con uv y núcleo analítico independiente | Aceptada |

## Plantilla

```markdown
# ADR-XXX: Título

- **Estado:** Propuesta | Aceptada | Reemplazada por ADR-YYY
- **Fecha:** AAAA-MM-DD

## Contexto
## Decisión
## Alternativas consideradas
## Consecuencias
```
