# ADR-007: Entorno híbrido Windows + WSL2 + Colab

- **Estado:** Aceptada
- **Fecha:** 2026-11-17

## Contexto

El equipo trabaja en Windows 11 (Intel i5-1135G7, 4 núcleos, 8 hilos, 15,7 GB, sin GPU NVIDIA). WSL2 con Ubuntu 26.04 ya tiene g++ 15.2, OpenMP y OpenMPI 5.0.10 funcionando. El detalle está en `05_Entorno_Desarrollo_HPC.md`.

## Decisión

| Entorno | Uso |
|---|---|
| Windows | Editor, Git, frontend, núcleo en modo secuencial |
| WSL2 Ubuntu | Backend completo, OpenMP, MPI, compilación de C++, PostgreSQL, benchmarks de CPU |
| Google Colab | CUDA y benchmarks de GPU |
| GitHub Actions (Ubuntu) | Integración continua, incluidas pruebas MPI |

- El repositorio permanece en el disco de Windows; el entorno virtual de WSL se guarda en el directorio personal de Linux (`UV_PROJECT_ENVIRONMENT`) por rendimiento.
- Docker Compose queda para el despliegue y la demostración, no es obligatorio en el desarrollo.

## Alternativas consideradas

| Alternativa | Motivo de descarte |
|---|---|
| Todo en Windows nativo | Requiere MS-MPI y MSVC Build Tools (~6 GB); difiere de Colab y de la CI. |
| Clonar el repositorio dentro de WSL | Más rápido en disco, pero el equipo usa GitHub Desktop en Windows. Se puede adoptar después. |
| Docker Desktop para todo | No está instalado; agrega consumo de memoria en un equipo de 15,7 GB. |

## Consecuencias

- Las mediciones de MPI y OpenMP se hacen en WSL; las de CUDA, en Colab.
- El código debe funcionar en Windows sin las piezas paralelas (respaldo secuencial).
