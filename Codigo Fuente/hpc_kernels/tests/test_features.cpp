// Prueba en C++ puro de los núcleos OpenMP: equivalencia con una versión ingenua,
// resultados idénticos con 1 y varios hilos, y tiempos con 1, 2, 4 y 8 hilos.
#include <algorithm>
#include <chrono>
#include <cmath>
#include <cstdio>
#include <random>
#include <vector>

#include "hpc_kernels/features.hpp"

namespace {

double naive_mean(const std::vector<double>& x, std::size_t T, std::size_t j, std::size_t t,
                  std::size_t w) {
  if (t + 1 < w) return std::nan("");
  double s = 0.0;
  for (std::size_t i = t + 1 - w; i <= t; ++i) {
    const double v = x[j * T + i];
    if (std::isnan(v)) return std::nan("");
    s += v;
  }
  return s / static_cast<double>(w);
}

bool same(double a, double b, double tol) {
  if (std::isnan(a) || std::isnan(b)) return std::isnan(a) && std::isnan(b);
  return std::fabs(a - b) <= tol * (1.0 + std::fabs(b));
}

}  // namespace

int main() {
  int failures = 0;

  // 1) Equivalencia con la versión ingenua (incluye NaN dentro de la ventana).
  {
    const std::size_t T = 300, N = 17, w = 7;
    std::vector<double> x(T * N), y(T * N);
    std::mt19937_64 gen(42);
    std::gamma_distribution<double> dist(2.0, 30.0);
    for (auto& v : x) v = dist(gen);
    x[5 * T + 40] = std::nan("");
    x[11 * T + 0] = std::nan("");
    hpc_kernels::rolling_mean(x.data(), y.data(), T, N, w, 4);
    for (std::size_t j = 0; j < N; ++j)
      for (std::size_t t = 0; t < T; ++t)
        if (!same(y[j * T + t], naive_mean(x, T, j, t, w), 1e-9)) ++failures;
    std::printf("equivalencia con version ingenua: %s\n", failures == 0 ? "OK" : "FALLA");
  }

  // 2) Mismos bits con 1 hilo y con 8 hilos; 3) tiempos.
  const std::size_t T = 1460, N = 2000, w = 28;
  std::vector<double> x(T * N), y1(T * N), yp(T * N);
  std::mt19937_64 gen(7);
  std::normal_distribution<double> dist(100.0, 15.0);
  for (auto& v : x) v = dist(gen);

  hpc_kernels::rolling_mean(x.data(), y1.data(), T, N, w, 1);
  hpc_kernels::rolling_mean(x.data(), yp.data(), T, N, w, 8);
  bool identical = true;
  for (std::size_t i = 0; i < T * N; ++i)
    if (!(y1[i] == yp[i] || (std::isnan(y1[i]) && std::isnan(yp[i])))) identical = false;
  std::printf("identico con 1 y 8 hilos: %s\n", identical ? "OK" : "FALLA");
  if (!identical) ++failures;

  std::printf("panel %zu x %zu, ventana %zu, hilos maximos %d\n", T, N, w,
              hpc_kernels::max_threads());
  double t1 = 0.0;
  for (int h : {1, 2, 4, 8}) {
    double best = 1e30;
    for (int rep = 0; rep < 5; ++rep) {
      const auto a = std::chrono::steady_clock::now();
      hpc_kernels::rolling_mean(x.data(), yp.data(), T, N, w, h);
      const auto b = std::chrono::steady_clock::now();
      best = std::min(best, std::chrono::duration<double>(b - a).count());
    }
    if (h == 1) t1 = best;
    std::printf("  hilos=%d  tiempo=%.4f s  aceleracion=%.2f  eficiencia=%.2f\n", h, best,
                t1 / best, t1 / best / h);
  }

  std::printf("%s\n", failures == 0 ? "TODAS LAS PRUEBAS OK" : "HAY FALLAS");
  return failures == 0 ? 0 : 1;
}
