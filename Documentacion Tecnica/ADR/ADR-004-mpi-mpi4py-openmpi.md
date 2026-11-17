# ADR-004: MPI con mpi4py sobre OpenMPI

- **Estado:** Aceptada
- **Fecha:** 2026-11-17

## Contexto

El OE3 exige procesar datos históricos con MPI. Las tareas a distribuir (series, orígenes de validación, semillas, configuraciones de hiperparámetros) son independientes y viven en Python. WSL ya tiene OpenMPI 5.0.10 y `mpiexec -n 4` funciona (ver `05_Entorno_Desarrollo_HPC.md`).

## Decisión

- Se usa **mpi4py** sobre **OpenMPI** en Linux (WSL, CI y Colab).
- `forecast_core.hpc.mpi` ofrece funciones de reparto (`scatter` por bloques equilibrados) y reunión (`gather` en el proceso raíz).
- Los pipelines se lanzan con `mpiexec -n p python -m forecast_core.pipelines.<pipeline> --config <yaml>`.
- MS-MPI en Windows es opcional y no forma parte del flujo oficial.

## Alternativas consideradas

| Alternativa | Motivo de descarte |
|---|---|
| MPI en C/C++ directamente | Obligaría a reescribir en C++ el entrenamiento y la evaluación que ya están en Python. Se reserva C++ para OpenMP. |
| `multiprocessing` de Python | No es MPI; no cumple el OE3. Sí sirve como comparación adicional. |
| Dask o Apache Spark | No es MPI; agregan infraestructura. Spark queda como línea futura si el volumen crece. |

## Consecuencias

- Las pruebas de MPI corren con `mpiexec -n 2` en la integración continua.
- Con 4 núcleos físicos, la eficiencia se mide hasta *p* = 4; *p* = 8 usa hilos lógicos y se reporta aparte.
