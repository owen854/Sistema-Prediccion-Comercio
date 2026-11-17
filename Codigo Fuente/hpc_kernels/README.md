# Núcleos C++ con OpenMP (`forecast_hpc_kernels`)

Cálculo de variables (media móvil, rezagos) sobre paneles *T × N* con varios hilos (RF-35; ADR-003). Se usan desde Python a través de `forecast_core.hpc.omp`, que cae a NumPy si el módulo no está compilado.

Se compilan en Linux (WSL, Colab, CI). En Windows no se compilan: se usa el respaldo NumPy.

## Compilar e instalar (WSL)

Desde `Codigo Fuente/backend`:

```bash
uv sync --extra kernels
```

## Prueba en C++ puro

```bash
cmake -S . -B build -DHPC_KERNELS_BUILD_TESTS=ON && cmake --build build && ./build/test_features
```

Sin CMake se puede compilar directamente:

```bash
g++ -O3 -fopenmp -Iinclude src/features_omp.cpp tests/test_features.cpp -o /tmp/test_features && /tmp/test_features
```

## Diseño PCAM

| Etapa | Decisión |
|---|---|
| Partición | Una tarea por serie (columna del panel) |
| Comunicación | Ninguna: cada hilo escribe solo su columna |
| Aglomeración | Bloques de columnas contiguas por hilo (`schedule(static)`) |
| Mapeo | Hilos OpenMP sobre los núcleos de la máquina |

La matriz se procesa en orden de columnas (Fortran) para que cada hilo recorra memoria contigua. El resultado es idéntico bit a bit con cualquier número de hilos, porque cada serie se calcula completa en un solo hilo.
