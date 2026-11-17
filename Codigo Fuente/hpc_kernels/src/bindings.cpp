// Enlace de los núcleos OpenMP con Python (pybind11).
#include <pybind11/numpy.h>
#include <pybind11/pybind11.h>

#include <stdexcept>

#include "hpc_kernels/features.hpp"

namespace py = pybind11;

// f_style + forcecast: pybind11 convierte la entrada a float64 en orden de columnas
// (copia solo si hace falta), que es la disposición que esperan los núcleos.
using FArray = py::array_t<double, py::array::f_style | py::array::forcecast>;

namespace {

FArray make_output(py::ssize_t T, py::ssize_t N) {
  return FArray({T, N}, {static_cast<py::ssize_t>(sizeof(double)),
                         static_cast<py::ssize_t>(sizeof(double)) * T});
}

void check_2d(const py::buffer_info& b) {
  if (b.ndim != 2) throw std::invalid_argument("Se esperaba una matriz (T, N).");
}

FArray rolling_mean(const FArray& x, py::ssize_t window, int threads) {
  if (window < 1) throw std::invalid_argument("window debe ser mayor o igual a 1.");
  const auto in = x.request();
  check_2d(in);
  const auto T = in.shape[0], N = in.shape[1];
  FArray out = make_output(T, N);
  auto o = out.request();
  {
    py::gil_scoped_release release;  // los hilos OpenMP corren sin el GIL
    hpc_kernels::rolling_mean(static_cast<const double*>(in.ptr), static_cast<double*>(o.ptr),
                              static_cast<std::size_t>(T), static_cast<std::size_t>(N),
                              static_cast<std::size_t>(window), threads);
  }
  return out;
}

FArray lag(const FArray& x, py::ssize_t k, int threads) {
  if (k < 0) throw std::invalid_argument("k debe ser mayor o igual a 0.");
  const auto in = x.request();
  check_2d(in);
  const auto T = in.shape[0], N = in.shape[1];
  FArray out = make_output(T, N);
  auto o = out.request();
  {
    py::gil_scoped_release release;
    hpc_kernels::lag(static_cast<const double*>(in.ptr), static_cast<double*>(o.ptr),
                     static_cast<std::size_t>(T), static_cast<std::size_t>(N),
                     static_cast<std::size_t>(k), threads);
  }
  return out;
}

}  // namespace

PYBIND11_MODULE(_core, m) {
  m.doc() = "Núcleos C++ con OpenMP para paneles T×N";
  m.def("rolling_mean", &rolling_mean, py::arg("x"), py::arg("window"), py::arg("threads") = 0,
        "Media móvil por serie (columna).");
  m.def("lag", &lag, py::arg("x"), py::arg("k"), py::arg("threads") = 0,
        "Rezago k por serie (columna).");
  m.def("max_threads", &hpc_kernels::max_threads, "Hilos máximos de OpenMP.");
  m.attr("openmp_version") = _OPENMP;
}
