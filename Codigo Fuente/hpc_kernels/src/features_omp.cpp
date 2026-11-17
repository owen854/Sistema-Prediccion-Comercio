#include "hpc_kernels/features.hpp"

#include <cmath>
#include <cstdint>
#include <limits>

#include <omp.h>

namespace hpc_kernels {

namespace {
constexpr double kNaN = std::numeric_limits<double>::quiet_NaN();

int resolve_threads(int threads) { return threads > 0 ? threads : omp_get_max_threads(); }

// Media móvil de una sola serie (contigua). Suma deslizante de los valores finitos
// y conteo de NaN dentro de la ventana: O(T) por serie.
void rolling_mean_series(const double* x, double* y, std::size_t T, std::size_t w) {
  double sum = 0.0;
  std::size_t nan_in_window = 0;
  for (std::size_t t = 0; t < T; ++t) {
    const double v = x[t];
    if (std::isnan(v)) {
      ++nan_in_window;
    } else {
      sum += v;
    }
    if (t >= w) {
      const double old = x[t - w];
      if (std::isnan(old)) {
        --nan_in_window;
      } else {
        sum -= old;
      }
    }
    y[t] = (t + 1 >= w && nan_in_window == 0) ? sum / static_cast<double>(w) : kNaN;
  }
}
}  // namespace

void rolling_mean(const double* in, double* out, std::size_t T, std::size_t N,
                  std::size_t window, int threads) {
  const auto n = static_cast<std::int64_t>(N);
#pragma omp parallel for schedule(static) num_threads(resolve_threads(threads))
  for (std::int64_t j = 0; j < n; ++j) {
    const std::size_t offset = static_cast<std::size_t>(j) * T;
    rolling_mean_series(in + offset, out + offset, T, window);
  }
}

void lag(const double* in, double* out, std::size_t T, std::size_t N, std::size_t k,
         int threads) {
  const auto n = static_cast<std::int64_t>(N);
#pragma omp parallel for schedule(static) num_threads(resolve_threads(threads))
  for (std::int64_t j = 0; j < n; ++j) {
    const std::size_t offset = static_cast<std::size_t>(j) * T;
    for (std::size_t t = 0; t < T; ++t) {
      out[offset + t] = t >= k ? in[offset + t - k] : kNaN;
    }
  }
}

int max_threads() { return omp_get_max_threads(); }

}  // namespace hpc_kernels
