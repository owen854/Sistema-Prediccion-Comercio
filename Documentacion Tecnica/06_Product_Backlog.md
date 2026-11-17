# Product Backlog

**Proyecto:** Sistema de Predicción de Demanda para el Comercio Minorista Fronterizo
**Actualizado:** 17/11/2026 (cierre técnico de la Fase 0)

Estado: ✅ Hecho · 🟡 En curso / pendiente de una acción del equipo · ⬜ Por hacer

---

## Sprint 0 — Fase 0: Arquitectura y cimientos

| ID | Historia | Estado | Evidencia o pendiente |
|---|---|---|---|
| HU-01 | Estructura de `Codigo Fuente/` con herramientas configuradas | ✅ | Estructura de la arquitectura (sección 10); ruff, mypy, pytest, ESLint, Vitest sin errores |
| HU-02 | Integración continua en cada *pull request* | 🟡 | `.github/workflows/ci.yml` creado (backend con MPI y núcleos, C++, frontend). Se verifica en GitHub al primer *push*. |
| HU-03 | Módulos del prototipo como paquete probado | ✅ | `tests/equivalence/test_regresion_prototipo.py`: resultados idénticos al prototipo; métricas, origen móvil y líneas base al 100 % de cobertura |
| HU-04 | Levantar base de datos, API y frontend con un comando | 🟡 | `docker-compose.yml` y Dockerfiles escritos, sin probar (Docker no está instalado). API y web verificadas por separado; en WSL, PostgreSQL lo instala `setup_wsl_hpc.sh`. |
| HU-05 | Comprobar MPI, OpenMP y CUDA en el hardware del equipo | 🟡 | OpenMP (C++) y MPI (C) verificados en WSL; `mpi4py` y la compilación con pybind11 se verifican al ejecutar `setup_wsl_hpc.sh`; CUDA con el cuaderno de Colab (requiere subir el código a GitHub). |
| — | Decisiones registradas (ADR-001 a ADR-008) | ✅ | `Documentacion Tecnica/ADR/` |
| — | Cuaderno del piloto LSTM en el repositorio | 🟡 | Falta que el equipo lo copie a `notebooks/legacy/` |
| — | Licencia del proyecto | 🟡 | Decisión del equipo y del director (derechos de autor, Ley 23 de 1982) |

---

## Sprint 1 — Fase 1: Comprensión del negocio y de los datos (OE1)

| ID | Historia | Criterio de aceptación | Pts | RF | Frente |
|---|---|---|---|---|---|
| HU-06 | Como analista, quiero descargar y versionar la EMC, el IPC y los flujos de Migración, para reproducir el OE1. | Cada fuente se descarga con un comando; manifiesto con hash; meses iguales a la Tabla IV del informe (164, 117, 174). | 8 | RF-01 a RF-03, RF-11 | F1 |
| HU-07 | Como analista, quiero el calendario de festivos y eventos de frontera, para usarlos como variables. | `configs/calendar_events.yaml` cargado; fechas marcadas "verificar" confirmadas con fuente; función que devuelve variables por fecha. | 3 | RF-05 | F1 |
| HU-08 | Como investigador, quiero regenerar las figuras y tablas del OE1 desde código. | `make reproduce-oe1` produce las Figuras 1 a 5 y Tablas III y IV; coinciden 4,2 % anual, +28,8 % en diciembre, +0,72 puntos y rezago de 1 mes. | 8 | RF-18 a RF-21, RF-23 | F1 |
| HU-09 | Como comerciante, quiero cargar mis ventas en una plantilla de Excel. | La carga valida la plantilla, explica errores y guarda los datos anonimizados y versionados. | 8 | RF-06 a RF-08 | F1 + F3 |
| HU-10 | Como integrante de HPC, quiero datos sintéticos de hasta 1.000 series. | Semilla fija; etiqueta sintética; más de un millón de filas en menos de 2 minutos. | 3 | RF-10, RNF-05 | F2 |
| HU-11 | Como analista, quiero las tablas de conjuntos de datos, series y observaciones con su API. | Migración Alembic; endpoints `GET/POST /api/v1/datasets` con pruebas de integración. | 5 | RF-59, RF-66 | F3 |
| HU-12 | Como equipo, quiero el formato de autorización de comercios (Ley 1581). | Documento aprobado por el director; registro de autorización en la base de datos. | 3 | RF-09 | Todos |

## Sprint 2 — Fase 2: Preparación y modelado secuencial (OE2)

| ID | Historia | Criterio de aceptación | Pts | RF | Frente |
|---|---|---|---|---|---|
| HU-13 | Como analista, quiero limpiar, agregar y construir variables por configuración. | Bitácora de ajustes; variables de `configs/features.yaml`; prueba de no fuga de información. | 8 | RF-12 a RF-16 | F1 |
| HU-14 | Como analista, quiero SARIMA/SARIMAX y Prophet con la interfaz común. | Modelos pasan las pruebas de la interfaz; experimentos e02 y e03 ejecutables. | 8 | RF-25, RF-26, RF-28 | F1 |
| HU-15 | Como investigador, quiero replicar el piloto LSTM en PyTorch. | Experimento e04: MAPE entre 3,6 % y 4,1 % o diferencia explicada. | 8 | RF-27 | F1 + F2 |
| HU-16 | Como investigador, quiero comparar modelos con semillas y registrar todo en MLflow. | Tabla comparativa con media y rango de 4 grupos de semillas; ejecución reproducible. | 5 | RF-29, RF-41, RF-42 | F1 |
| HU-17 | Como investigador, quiero medir el aporte de las variables fronterizas. | Experimento e05 con y sin flujos; resultado reportado tal cual. | 3 | RF-44 | F1 |
| HU-18 | Como integrante de HPC, quiero el diseño PCAM detallado de cada etapa. | ADR con partición y comunicación por etapa; actualiza la Tabla VIII del informe. | 3 | OE2 | F2 |
| HU-19 | Como usuario, quiero iniciar sesión con mi rol y ver solo los datos de mi comercio. | Login, tokens, roles y aislamiento por comercio con pruebas de permisos. | 8 | RF-62, RF-63 | F3 |
| HU-20 | Como analista, quiero lanzar entrenamientos como trabajos en segundo plano. | Worker con `SKIP LOCKED`; estados y progreso visibles en la API. | 8 | RF-64 | F3 |

Las épicas de los Sprints 3 a 6 están en `04_Plan_Gestion_Proyecto.md`, sección 7.1; sus historias se detallan en el refinamiento de cada sprint.
