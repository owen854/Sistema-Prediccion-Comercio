# ADR-003: OpenMP con núcleos C++ expuestos con pybind11

- **Estado:** Aceptada
- **Fecha:** 2026-11-17

## Contexto

El documento indica "C/C++ con OpenMP, MPI y CUDA para las implementaciones paralelas" y "Python para el modelado". El cálculo de variables (rezagos, medias móviles, variaciones anuales) sobre la matriz *T × N* es paralelizable por serie y se beneficia de memoria compartida (Tabla VIII del informe).

## Decisión

- Los núcleos se escriben en **C++17 con OpenMP** en `Codigo Fuente/hpc_kernels/`.
- Se exponen a Python con **pybind11** y se compilan con **scikit-build-core + CMake** como módulo `forecast_hpc_kernels`.
- `forecast_core.hpc.omp` usa el módulo compilado si existe y, si no, una **implementación de referencia en NumPy** con la misma interfaz (RF-34, RNF-13).
- Las pruebas de equivalencia comparan ambas implementaciones (RF-39).

## Alternativas consideradas

| Alternativa | Motivo de descarte |
|---|---|
| Numba con `prange` (capa de hilos OpenMP) | Más simple, pero no es C/C++ como pide el documento y oculta las directivas OpenMP. |
| Cython con `prange` | Mezcla de lenguajes menos legible que C++ puro para el informe. |
| Compilar en Windows con MSVC | Requiere ~6 GB de Build Tools; el g++ de MSYS2 no es compatible con el Python oficial. |

## Consecuencias

- El módulo compilado se construye en Linux (WSL, Colab, CI). En Windows se usa el respaldo NumPy.
- Las directivas OpenMP quedan visibles en el código, lo que facilita explicarlas en la monografía.
