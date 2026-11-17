cmake_minimum_required(VERSION 3.18)
project(forecast_hpc_kernels LANGUAGES CXX)

set(CMAKE_CXX_STANDARD 17)
set(CMAKE_CXX_STANDARD_REQUIRED ON)
set(CMAKE_POSITION_INDEPENDENT_CODE ON)

find_package(OpenMP REQUIRED COMPONENTS CXX)

# Biblioteca con los núcleos (independiente de Python): se prueba también en C++ puro.
add_library(hpc_features STATIC src/features_omp.cpp)
target_include_directories(hpc_features PUBLIC ${CMAKE_CURRENT_SOURCE_DIR}/include)
target_link_libraries(hpc_features PUBLIC OpenMP::OpenMP_CXX)
target_compile_options(hpc_features PRIVATE -O3 -Wall -Wextra)

# Módulo de Python (solo cuando lo construye scikit-build-core).
if(SKBUILD)
  find_package(Python REQUIRED COMPONENTS Interpreter Development.Module)
  find_package(pybind11 CONFIG REQUIRED)
  pybind11_add_module(_core MODULE src/bindings.cpp)
  target_link_libraries(_core PRIVATE hpc_features)
  install(TARGETS _core DESTINATION forecast_hpc_kernels)
endif()

# Prueba en C++ puro:  cmake -S . -B build -DHPC_KERNELS_BUILD_TESTS=ON && cmake --build build && ctest --test-dir build
option(HPC_KERNELS_BUILD_TESTS "Compilar la prueba en C++ de los núcleos" OFF)
if(HPC_KERNELS_BUILD_TESTS)
  enable_testing()
  add_executable(test_features tests/test_features.cpp)
  target_link_libraries(test_features PRIVATE hpc_features)
  add_test(NAME test_features COMMAND test_features)
endif()
