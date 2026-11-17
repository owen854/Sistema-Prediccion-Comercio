// Núcleos de variables sobre paneles T×N con OpenMP (RF-35; ADR-003).
//
// Disposición de memoria: orden por columnas (Fortran). La serie j ocupa las
// posiciones [j*T, (j+1)*T), así cada hilo recorre memoria contigua.
//
// PCAM:
//   Partición     -> una tarea por serie (columna).
//   Comunicación  -> ninguna: cada hilo escribe solo su columna de salida.
//   Aglomeración  -> bloques de columnas por hilo (schedule(static)).
//   Mapeo         -> hilos OpenMP sobre los núcleos de la máquina.
#pragma once

#include <cstddef>

namespace hpc_kernels {

// Media móvil de ventana `window` por serie. NaN si faltan periodos al inicio o si
// hay algún NaN dentro de la ventana (misma semántica que
// pandas.rolling(window, min_periods=window).mean()).
// `threads <= 0` usa el número de hilos por defecto de OpenMP.
void rolling_mean(const double* in, double* out, std::size_t T, std::size_t N,
                  std::size_t window, int threads);

// Rezago `k` por serie; las primeras k filas quedan en NaN.
void lag(const double* in, double* out, std::size_t T, std::size_t N, std::size_t k,
         int threads);

// Hilos máximos que usaría OpenMP.
int max_threads();

}  // namespace hpc_kernels
