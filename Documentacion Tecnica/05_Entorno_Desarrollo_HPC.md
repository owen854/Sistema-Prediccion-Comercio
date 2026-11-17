# Entorno de Desarrollo y Cómputo Paralelo

**Proyecto:** Sistema de Predicción de Demanda para el Comercio Minorista Fronterizo
**Versión:** 1.0 — 17/11/2026
**Resultado del *spike* de infraestructura de la Fase 0 (actividad 0.7).**

---

## 1. Conclusión

**Sí se puede desarrollar todo el sistema desde este equipo**, repartiendo el trabajo así:

| Dónde | Qué corre | Por qué |
|---|---|---|
| **Windows** | Editor, Git, frontend (Next.js), pruebas rápidas del núcleo en modo secuencial | Es el entorno diario del equipo. |
| **WSL2 Ubuntu** (en este mismo equipo) | Backend completo, OpenMP, MPI, compilación de núcleos C++, PostgreSQL, benchmarks de CPU | Ya tiene OpenMPI 5.0.10, g++ 15.2 y OpenMP funcionando; es Linux como Colab y la integración continua. |
| **Google Colab** (GPU NVIDIA remota) | Entrenamiento de la LSTM con CUDA y benchmarks de GPU | El equipo no tiene GPU NVIDIA. |
| **GitHub Actions** | Integración continua: lint, tipos, pruebas, pruebas MPI con 2 procesos, compilación | Verificación automática en cada *pull request*. |

> **Colab no reemplaza a CUDA: es el lugar donde corre CUDA.** PyTorch en Colab usa CUDA sobre la GPU de Google (normalmente una NVIDIA T4). El OE3 se sigue cumpliendo tal como está redactado ("entrenar modelos de deep learning con CUDA"); solo cambia la máquina donde se ejecuta.

---

## 2. Verificación realizada en este equipo

| Recurso | Resultado |
|---|---|
| CPU | Intel Core i5-1135G7: 4 núcleos físicos, 8 hilos, 15,7 GB de RAM |
| GPU | Intel Iris Xe (sin CUDA) |
| WSL | Versión 2, Ubuntu 26.04.1 LTS, 8 CPU visibles, ~7 GB de RAM asignados, 953 GB libres |
| Compilador en WSL | g++ 15.2.0, `build-essential` instalado |
| OpenMP en WSL | **Funciona**: programa de prueba ejecutó 8 hilos |
| MPI en WSL | **Funciona**: OpenMPI 5.0.10 ya instalado; `mpiexec -n 4` y `mpiexec -n 8 --oversubscribe` con `MPI_Reduce` correcto |
| CMake en WSL | **Falta** (disponible en apt: 4.2.3) |
| Encabezados de Python en WSL | **Faltan** (`python3-dev`); no son necesarios si se usa el Python que instala uv |
| uv en WSL | **Falta** |
| PostgreSQL en WSL | **Falta** (disponible en apt: versión 18) |
| Repositorio en GitHub | Público: Colab lo puede clonar sin credenciales |

### 2.1 Resultados del *spike* (Fase 0)

**OpenMP en C++** (`hpc_kernels/tests/test_features.cpp`, compilado con g++ 15.2 en WSL): media móvil de 28 días sobre un panel sintético de 1.460 días × 2.000 series, mejor de 5 repeticiones.

| Hilos | Tiempo | Aceleración | Eficiencia |
|---|---|---|---|
| 1 | 6,5 ms | 1,00 | 1,00 |
| 2 | 3,4 ms | 1,90 | 0,95 |
| 4 | 2,4 ms | 2,64 | 0,66 |
| 8 | 5,5 ms | 1,18 | 0,15 |

- El resultado es **idéntico bit a bit** con 1 y con 8 hilos, y coincide con una implementación ingenua (incluidos los `NaN`).
- Con 8 hilos empeora: la máquina tiene 4 núcleos físicos (8 hilos lógicos comparten núcleo) y una sola media móvil es una operación limitada por la memoria que tarda milisegundos, así que el costo de coordinar hilos pesa más que el cálculo. **Lección para la Fase 3:** calcular varias variables en una sola pasada por serie (más trabajo por hilo) y medir con *h* ≤ 4.

**MPI en C** (OpenMPI 5.0.10, WSL): `MPI_Reduce` correcto con 4 y con 8 procesos.

**Backend en Windows:** el núcleo corre en modo secuencial con respaldo NumPy; 49 pruebas aprobadas, incluida la que confirma que los módulos migrados reproducen exactamente los resultados del prototipo.

### 2.2 Estado después de `setup_wsl_hpc.sh` (17/11/2026)

| Componente | Estado |
|---|---|
| CMake 4.2.3, Ninja, uv 0.13.9 | Instalados |
| Entorno de Python | `~/.venvs/prediccion-demanda`, Python 3.12.16; `UV_PROJECT_ENVIRONMENT` en `~/.bashrc` |
| Núcleo OpenMP (`forecast_hpc_kernels`) | Compilado con pybind11; 8 hilos, OpenMP 4.5 (`_OPENMP = 201511`) |
| mpi4py | Funciona sobre OpenMPI 5.0.10 |
| PostgreSQL | Activo; migración `0001` aplicada (`comercio`, `usuario`, `trabajo`) |
| Pruebas | **69 aprobadas, ninguna omitida** (`pytest -m "not cuda"`), incluidas equivalencia OpenMP y MPI con 2 y 3 procesos |

La integración continua de GitHub (Ubuntu) da el mismo resultado: backend, núcleos C++ y frontend en verde.

### 2.3 Primeros benchmarks desde Python (WSL, datos sintéticos)

**MPI** — validación con origen móvil (24 particiones, horizonte 14, paso 7) sobre 500 series × 1.460 días; el proceso raíz genera el panel y lo envía a los demás (`bcast`). Mediana de 8 corridas por configuración:

| Procesos | Tiempo | Aceleración | Eficiencia |
|---|---|---|---|
| 1 | 1,78 s | 1,00 | 1,00 |
| 2 | 1,06 s | 1,68 | 0,84 |
| 4 | 0,78 s | 2,28 | 0,57 |
| 8 (sobresuscripción) | 0,82 s | 2,18 | 0,27 |

- Fracción paralelizable estimada con la ley de Amdahl: ***f* ≈ 0,69**. La parte secuencial incluye en buena medida el envío del panel completo a cada proceso.
- Con 8 procesos no mejora: el equipo tiene 4 núcleos físicos.
- **Lección para la Fase 3:** repartir solo los bloques de series que necesita cada proceso, o que cada proceso lea su parte del Parquet, en lugar de enviar el panel completo.

**OpenMP** — media móvil de 28 días sobre 1.460 días × 2.000 series, mediana de 5 repeticiones:

| Implementación | Hilos | Tiempo | Aceleración (frente a 1 hilo) |
|---|---|---|---|
| Referencia NumPy/pandas | 1 | 73 ms | — |
| Núcleo C++ desde Python | 1 | 13,3 ms | 1,00 |
| Núcleo C++ desde Python | 2 | 10,9 ms | 1,22 |
| Núcleo C++ desde Python | 4 | 13,0 ms | 1,02 |
| Núcleo C++ desde Python | 8 | 10,9 ms | 1,22 |

- El núcleo C++ es unas **5,5 veces más rápido que la referencia NumPy**, y el resultado es idéntico con cualquier número de hilos.
- La aceleración por hilos desde Python es baja, cuando en C++ puro llegaba a 1,90× con 2 hilos (sección 2.1). La causa más probable es que en cada llamada el enlace reacomoda la matriz de orden por filas (C) a orden por columnas (Fortran), y esa copia no se paraleliza.
- **Lección para la Fase 3:** guardar el panel una sola vez en orden por columnas y calcular varias variables en la misma pasada, para que el trabajo paralelo domine sobre la copia.

Resultados completos con la descripción del hardware en `Codigo Fuente/experiments/results/spike/` (no versionado). Para mediciones limpias, vaciar esa carpeta antes de cada campaña: el resumen MPI agrupa todas las corridas que encuentre.

---

## 3. Instalación

### 3.1 WSL2 Ubuntu (obligatorio)

MPI **ya está instalado** en WSL. Solo falta CMake y unas herramientas complementarias. Abre la terminal de Ubuntu (menú Inicio → "Ubuntu") y ejecuta:

```bash
sudo apt update
```

```bash
sudo apt install -y cmake ninja-build pkg-config python3-dev python3-venv postgresql
```

Instala uv (gestor de entornos de Python, sin `sudo`; script oficial de Astral):

```bash
curl -LsSf https://astral.sh/uv/install.sh | sh
```

Cierra y vuelve a abrir la terminal, y comprueba:

```bash
cmake --version && mpiexec --version && uv --version
```

**Atajo:** todo lo anterior, más la creación del entorno del proyecto y las pruebas, lo hace el script del repositorio:

```bash
bash "/mnt/c/Users/PC/Documents/GitHub/Sistema-Prediccion-Comercio/Codigo Fuente/scripts/setup_wsl_hpc.sh"
```

El script pide la contraseña de Ubuntu una vez (para `apt`).

### 3.2 Memoria de WSL (recomendado)

WSL usa por defecto la mitad de la RAM (~7 GB). Para los benchmarks con más de un millón de filas conviene subirla a 10 GB. Crea el archivo `C:\Users\PC\.wslconfig` con:

```ini
[wsl2]
memory=10GB
processors=8
```

y reinicia WSL desde PowerShell:

```powershell
wsl --shutdown
```

### 3.3 Windows (opcional)

No hace falta instalar MPI ni CMake en Windows: el núcleo funciona en Windows en modo secuencial (con respaldo en NumPy) y todo lo paralelo se ejecuta en WSL. Solo si algún integrante quiere ejecutar MPI nativo en Windows:

| Herramienta | Instalación | Nota |
|---|---|---|
| MS-MPI | Instalar `msmpisetup.exe` desde la página oficial de Microsoft MPI (v10.1.x) | Después, `uv pip install mpi4py` en el entorno de Windows. |
| CMake | `winget install Kitware.CMake` | Solo sirve si además se instala MSVC. |
| MSVC (Build Tools) | `winget install Microsoft.VisualStudio.2022.BuildTools` con la carga "Desarrollo de escritorio con C++" (~6 GB) | Necesario para compilar extensiones de Python en Windows; el g++ de MSYS2 no es compatible con el Python oficial. **No recomendado**: WSL ya resuelve esto. |

### 3.4 Editor

Se recomienda VS Code con la extensión **WSL**: se abre la carpeta del repositorio desde Ubuntu (`code .`) y el terminal, el intérprete de Python y las pruebas corren en Linux, mientras los archivos siguen en `C:\Users\PC\Documents\GitHub\…`.

El entorno virtual de Python de WSL se guarda en el directorio personal de Linux (no en `/mnt/c`), porque el acceso a disco de Windows desde WSL es lento. El script de instalación lo configura con la variable `UV_PROJECT_ENVIRONMENT`.

---

## 4. Uso de Google Colab para CUDA

### 4.1 Flujo de trabajo

1. Se sube el código a GitHub (rama de trabajo o `main`).
2. En Colab: *Entorno de ejecución → Cambiar tipo de entorno → GPU T4*.
3. Se abre `Codigo Fuente/infra/gpu_remota/run_cuda_experiments.ipynb`, que:
   - verifica la GPU (`nvidia-smi`, `torch.cuda.is_available()`);
   - clona el repositorio y la rama indicada;
   - instala el paquete `forecast_core` con sus dependencias de deep learning;
   - ejecuta el experimento o benchmark con su archivo YAML;
   - guarda resultados, métricas y la descripción del hardware en Google Drive.
4. Los resultados se descargan a `Codigo Fuente/experiments/` y se registran como cualquier otra ejecución.

### 4.2 Limitaciones de Colab y cómo se manejan

| Limitación | Efecto | Mitigación |
|---|---|---|
| Sesiones de hasta ~12 h y desconexión por inactividad (~90 min) | Un entrenamiento largo puede cortarse | Guardar puntos de control en Drive cada N épocas; experimentos divididos en tareas cortas. |
| La GPU gratuita no está garantizada y puede cambiar de modelo | Resultados de tiempo no comparables entre sesiones | **Medir CPU y GPU en la misma sesión de Colab** y registrar el modelo de GPU y CPU en cada ejecución. |
| Almacenamiento temporal | Se pierden archivos al cerrar | Escribir resultados en Google Drive. |
| Solo ~2 vCPU | MPI en Colab no es representativo | Los benchmarks de MPI y OpenMP se hacen en WSL (4 núcleos, 8 hilos). |
| Una sola GPU | La combinación MPI + CUDA se limita a varios procesos compartiendo una GPU | Demostrarla con *p* = 2 en Colab; si se necesita más, usar **Kaggle** (hasta 2 GPU T4, 30 h semanales gratis) o el laboratorio de la universidad. |
| Ventaja de la GPU poco visible con modelos pequeños | Una LSTM de 8 unidades sobre 162 meses es demasiado pequeña para la GPU | Medir el escenario donde la GPU sí aporta: muchas series entrenadas a la vez (datos sintéticos de 100 a 1.000 series) y búsqueda de hiperparámetros, como recomienda la revisión sistemática. |

### 4.3 Regla de medición

Para que la aceleración sea válida, **T₁ y Tₚ se miden en la misma máquina**:

| Tecnología | Máquina | Comparación |
|---|---|---|
| OpenMP | WSL en este equipo | 1 hilo frente a 2, 4 y 8 hilos |
| MPI | WSL en este equipo | 1 proceso frente a 2, 4 (y 8 con sobresuscripción, reportado aparte) |
| CUDA | Misma sesión de Colab | CPU de Colab frente a GPU de Colab |
| MPI + CUDA | Misma sesión de Colab o Kaggle | 1 proceso frente a 2 procesos compartiendo GPU (o 2 GPU en Kaggle) |

Cada ejecución guarda en su registro: CPU, núcleos, RAM, GPU, versión de CUDA, versión de PyTorch y sistema operativo.

---

## 5. Consecuencias en los requerimientos

| Requerimiento | Ajuste |
|---|---|
| RF-37 (CUDA) | Se cumple en Colab; el sistema detecta la GPU y, si no la hay, continúa en CPU (RNF-13). |
| RF-36 + RF-37 (MPI + CUDA) | Se demuestra con procesos que comparten una GPU; con varias GPU solo si se consigue Kaggle o laboratorio. |
| RNF-03 (eficiencia MPI) | Se mide en WSL con *p* ≤ 4 núcleos físicos. Con 8 procesos se usan hilos lógicos y se reporta por separado. |
| RNF-04 (aceleración CUDA) | Se mide en la misma sesión de Colab, con muchas series simultáneas. |
| RNF-08 (multiplataforma) | Windows ejecuta el sistema en modo secuencial; Linux (WSL, Colab, CI) ejecuta todo. |
