# Plan de Gestión del Proyecto

**Proyecto:** Sistema de Predicción de Demanda para el Comercio Minorista Fronterizo
**Metodología:** CRISP-DM adaptada con PCAM, ejecutada con Scrum
**Versión:** 1.0 — 16/11/2026
**Documentos relacionados:** `01_Requerimientos_RF_RNF.md`, `02_Evaluacion_Prototipo.md`, `03_Arquitectura_Sistema.md`

---

## 1. Propósito

Este plan organiza el desarrollo completo del sistema en fases, desde la arquitectura hasta la entrega. Parte del plan de dos semanas propuesto (`Plan_Trabajo_CRISP_DM_Scrum.md`) y lo ajusta para **priorizar la calidad del producto** y para cubrir todo lo que exigen los objetivos del documento del proyecto, en especial el cómputo paralelo (OE3) y la validación de inventarios (OE4), que el plan original no contemplaba.

## 2. Supuestos y restricciones

| # | Supuesto o restricción | Consecuencia en el plan |
|---|---|---|
| S1 | Equipo de 3 integrantes con dedicación parcial (estimada en 15 a 20 horas por semana cada uno). | Tres frentes de trabajo en paralelo; la velocidad real se calibra al cerrar el Sprint 1. |
| S2 | Hay tolerancia en las fechas; la prioridad es la calidad. | Plan base de 7 semanas, con una variante comprimida de 4 semanas (sección 8). |
| S3 | La fecha límite de entrega no está definida en la documentación. | Las fechas se expresan en semanas relativas; el equipo las fija con su calendario académico. |
| S4 | El equipo revisado no tiene GPU NVIDIA ni MPI instalado (ver `02_Evaluacion_Prototipo.md`, sección 9). | La Fase 0 incluye un *spike* de infraestructura HPC para asegurar GPU y MPI. |
| S5 | No hay todavía datos transaccionales autorizados de comercios. | La gestión para obtenerlos empieza en el Sprint 1; la validación tiene plan alterno (riesgo R1). |
| S6 | El OE1 y el OE2 ya tienen evidencia (informe IEEE), pero no está en código reproducible. | La Fase 1 y la Fase 2 deben **reproducir** esas cifras desde el código antes de ampliarlas. |

---

## 3. Ajustes al plan de dos semanas

| Aspecto | Plan original | Plan ajustado | Motivo |
|---|---|---|---|
| Duración | 2 semanas (2 sprints) | 7 semanas (Sprint 0 + 6 sprints de una semana) | El alcance completo (tres modelos, OpenMP, MPI, CUDA, API, seguridad, dashboard, validación) no cabe en dos semanas con calidad. |
| Fases | 7 fases CRISP-DM | Fase 0 de arquitectura + 6 fases CRISP-DM con PCAM | Pedido del equipo y metodología del documento (CRISP-DM + PCAM). |
| Modelos | Regresión lineal, Prophet, XGBoost, LightGBM, Random Forest | ARIMA/SARIMA, Prophet y LSTM con líneas base ingenuas; *boosting* como opcional | Son los algoritmos que fija el documento (OE2 y Tabla 2). |
| Cómputo paralelo | No aparece | Fase 3 completa: OpenMP, MPI, CUDA, equivalencia y aceleración | Es el núcleo del OE3 y de la pregunta de investigación. |
| Validación | División cronológica simple | Origen móvil, grupos de semillas, repeticiones, pruebas de significancia | Condiciones experimentales de la Tabla 2 y recomendaciones de la revisión sistemática. |
| Métricas | RMSE, MAE, MAPE (meta < 15 %) | Se mantienen, más WAPE o MASE para series con ceros, indicadores de inventario y de rendimiento paralelo | OE3 y OE4. La meta de 15 % se conserva para producto o categoría semanal. |
| Datos procesados | `data/processed/ventas_v1.csv` | Paneles versionados en Parquet con manifiesto y hash | Reproducibilidad (RNF-27). |
| Dashboard | Streamlit o Power BI | Next.js + FastAPI | Evaluación del prototipo (Power BI tiene costo de licencia; Next.js reutiliza el prototipo). |
| Revisión | Sprint Review en los días 7 y 14 | Sprint Review cada semana con demostración funcional | Retroalimentación temprana. |
| Calidad | Implícita | Definición de Hecho, integración continua, pruebas y revisión de código | Prioridad del equipo. |

---

## 4. Marco de trabajo

### 4.1 Integración de CRISP-DM, PCAM y Scrum

CRISP-DM y PCAM definen **qué** se construye en cada fase; Scrum define **cómo** se organiza el trabajo semana a semana. Cada fase se ejecuta en uno o más sprints, y cada sprint termina con un incremento funcional que se demuestra.

| Fase del plan | CRISP-DM | PCAM | Objetivo | Sprints |
|---|---|---|---|---|
| Fase 0. Arquitectura y cimientos | — | — | Habilita todos | Sprint 0 |
| Fase 1. Comprensión del negocio y de los datos | Comprensión del negocio y de los datos | — | OE1 | Sprint 1 |
| Fase 2. Preparación de datos y modelado secuencial | Preparación de datos; selección de técnicas | Partición y comunicación (diseño) | OE2 | Sprint 2 |
| Fase 3. Sistema paralelo | Modelado | Aglomeración y mapeo | OE3 | Sprints 3 y 4 |
| Fase 4. Plataforma: API, inventario y dashboard | Despliegue (parcial) | — | OG, OE3 | Sprints 2 a 5 (frente paralelo) |
| Fase 5. Evaluación y validación | Evaluación | — | OE4 | Sprint 5 |
| Fase 6. Despliegue, documentación y cierre | Despliegue | — | OG | Sprint 6 |

### 4.2 Roles

| Rol | Responsable | Responsabilidades |
|---|---|---|
| **Product Owner** | Director del proyecto (o un integrante como representante) | Prioriza el backlog, acepta o rechaza historias en la Sprint Review, cuida la alineación con los objetivos. |
| **Scrum Master** | Rotativo por sprint entre los integrantes | Facilita las ceremonias, elimina bloqueos, vigila la Definición de Hecho. |
| **Equipo de desarrollo** | Los tres integrantes | Construye el incremento. Cada integrante lidera un frente y revisa el código de otro frente. |

**Frentes de trabajo** (la asignación de personas la decide el equipo según sus fortalezas):

| Frente | Alcance | Fases principales |
|---|---|---|
| **F1. Datos y modelos** | Ingesta, calidad, EDA, variables, SARIMA, Prophet, LSTM, evaluación | 1, 2, 5 |
| **F2. Cómputo paralelo** | Núcleos OpenMP, MPI, CUDA, equivalencia, benchmarks | 0 (*spike*), 3, 5 |
| **F3. Plataforma** | Base de datos, API, seguridad, worker, inventario, frontend, despliegue | 0, 4, 6 |

### 4.3 Ceremonias

| Ceremonia | Frecuencia | Duración | Resultado |
|---|---|---|---|
| Sprint Planning | Inicio de cada sprint | 1 h | Objetivo del sprint y sprint backlog con historias estimadas |
| Daily Standup | Diaria (presencial, llamada o mensaje con formato fijo) | 10–15 min | Qué hice, qué haré, qué me bloquea |
| Refinamiento del backlog | A mitad de sprint | 30 min | Historias del siguiente sprint listas (Definición de Listo) |
| Sprint Review | Cierre de cada sprint | 45 min | Demostración del incremento; aceptación por el Product Owner |
| Retrospectiva | Cierre de cada sprint | 30 min | Una o dos acciones de mejora concretas para el siguiente sprint |

### 4.4 Artefactos

- **Product Backlog** en GitHub Projects, con épicas e historias trazadas a los RF y RNF.
- **Sprint Backlog** con columnas: Por hacer · En curso · En revisión · Hecho.
- **Incremento** etiquetado en Git al final de cada sprint (`v0.0`, `v0.1`, …, `v1.0`).
- **Gráfico de avance** (burndown) por sprint y porcentaje de requerimientos *Must* completados.

### 4.5 Definición de Listo (DoR)

Una historia entra a un sprint solo si:

1. Tiene criterios de aceptación verificables.
2. Está trazada a uno o más RF o RNF.
3. Está estimada en puntos de historia.
4. Sus dependencias (datos, decisiones, otras historias) están resueltas.

### 4.6 Definición de Hecho (DoD)

Una historia está terminada solo si:

1. El código está en una rama con *pull request* aprobado por un integrante de **otro frente**.
2. La integración continua está en verde: ruff, mypy, ESLint, compilación y pruebas.
3. Tiene pruebas automatizadas y la cobertura del módulo no baja.
4. Los parámetros están en archivos de configuración, sin valores quemados.
5. Los experimentos que produce están registrados en MLflow con semilla y versión de datos.
6. La documentación está actualizada (docstrings, README del módulo y ADR si hubo una decisión).
7. No incluye datos privados, secretos ni cifras sin origen.
8. Se demostró en la Sprint Review y el Product Owner la aceptó.

---

## 5. Fases del proyecto

### Fase 0 — Arquitectura y cimientos (Sprint 0, semana 1)

**Objetivo:** dejar listas la arquitectura, la jerarquía de carpetas de `Codigo Fuente/` y el entorno de todos los integrantes, para que las fases siguientes solo agreguen funcionalidad.

| # | Actividad | Frente | Requerimientos |
|---|---|---|---|
| 0.1 | Revisar y aprobar requerimientos, evaluación y arquitectura; registrar las decisiones como ADR (stack, cola de trabajos en PostgreSQL, OpenMP con pybind11, MPI con mpi4py, CUDA con PyTorch, MLflow). | Todos | — |
| 0.2 | Crear la jerarquía de carpetas y archivos de `Codigo Fuente/` según `03_Arquitectura_Sistema.md`, sección 10, con README por módulo. | F3 | RNF-23 |
| 0.3 | Configurar herramientas: uv y `pyproject.toml`, ruff, mypy, pytest, pre-commit, ESLint, Prettier, GitHub Actions, plantillas de PR, `.gitignore` de datos y licencia del proyecto. | F3 | RNF-22, RNF-24 |
| 0.4 | Migrar del prototipo A, con pruebas: métricas, origen móvil, línea base, panel T×N, reporte de calidad, generador sintético y TRM. | F1 | RF-10, RF-16, RF-24, RF-41 |
| 0.5 | Base del frontend: trasladar el diseño del prototipo B a `frontend/` sin Drizzle, sin *seed* y sin cifras fijas; navegación y cliente de la API. | F3 | RNF-10 |
| 0.6 | Base del backend: FastAPI con `/health`, configuración por entorno, PostgreSQL con Docker Compose y primera migración de Alembic. | F3 | RF-66, RNF-08 |
| 0.7 | *Spike* de infraestructura HPC: OpenMPI, CMake y g++ en WSL2; `mpiexec -n 4` con mpi4py; un núcleo OpenMP compilado con pybind11; PyTorch con CUDA en la GPU disponible (equipo de un integrante, laboratorio, Colab o Kaggle). | F2 | RF-35 a RF-37 |
| 0.8 | Incorporar al repositorio el cuaderno de Colab del piloto LSTM (`notebooks/legacy/`). | F1 | RNF-28 |
| 0.9 | Crear el Product Backlog con épicas e historias trazadas a los RF. | Todos | — |

**Criterios de salida:**
- La integración continua ejecuta `pytest` y `npm run build` en verde.
- `docker compose up` levanta base de datos, API y frontend.
- Cada integrante ejecuta el entorno de desarrollo en su equipo.
- El *spike* HPC está documentado, con la GPU que se usará identificada.
- El backlog está priorizado para los Sprints 1 y 2.

**Entregables:** `Codigo Fuente/` estructurado, ADR iniciales, pipeline de integración continua, backlog. Versión `v0.0`.

### Fase 1 — Comprensión del negocio y de los datos (Sprint 1, semana 2) → OE1

**Objetivo:** reproducir desde el código la evidencia del OE1 y dejar lista la entrada de datos de comercios.

| # | Actividad | Frente | Requerimientos |
|---|---|---|---|
| 1.1 | Ingestores de la EMC, el IPC por ciudades, Migración Colombia y la TRM, con manifiesto y hash. | F1 | RF-01 a RF-04, RF-11 |
| 1.2 | Calendario de eventos: festivos, quincenas, diciembre, cierres y reaperturas de la frontera con fuente. | F1 | RF-05 |
| 1.3 | Validación de esquema y reporte de calidad ampliado. | F1 | RF-07 |
| 1.4 | Módulo EDA: descomposición, crecimiento, inflación local y correlación cruzada con la frontera. | F1 | RF-18 a RF-21, RF-23 |
| 1.5 | Plantilla de carga transaccional, anonimización y registro de autorización. | F1 + F3 | RF-06, RF-08, RF-09 |
| 1.6 | Generador sintético escalable (100 a 1.000 series; más de un millón de filas). | F2 | RF-10, RNF-05 |
| 1.7 | Esquema de base de datos para comercios, conjuntos de datos, series y observaciones; API de carga y consulta. | F3 | RF-59, RF-66 |
| 1.8 | Gestión con comercios: contactar MIPYMES, presentar el formato de autorización (Ley 1581) y acordar la entrega de datos. | Todos | RF-09, R1 |

**Criterios de salida:**
- Un comando (`make reproduce-oe1`) regenera las Tablas III y IV y las Figuras 1 a 5 del informe; las cifras coinciden salvo por redondeo, o la diferencia queda explicada.
- Un CSV de ejemplo se carga de extremo a extremo y queda anonimizado, validado y versionado.

**Entregables:** `notebooks/01_patrones_consumo_OE1.ipynb`, reporte de calidad, pipeline de ingesta. Versión `v0.1`.

### Fase 2 — Preparación de datos y modelado secuencial (Sprint 2, semana 3) → OE2

**Objetivo:** tener los tres algoritmos del documento y las líneas base funcionando en modo secuencial, comparados bajo las mismas condiciones, y reproducir el piloto de la LSTM.

| # | Actividad | Frente | Requerimientos |
|---|---|---|---|
| 2.1 | Limpieza, agregación y panel T×N; variables configurables. | F1 | RF-12 a RF-15 |
| 2.2 | Particiones cronológicas y origen móvil, con prueba automática de no fuga de información. | F1 | RF-16 |
| 2.3 | Interfaz `Forecaster`; modelos ingenuos, SARIMA/SARIMAX y Prophet. | F1 | RF-24 a RF-26, RF-28 |
| 2.4 | LSTM en PyTorch (CPU) que replica el piloto: 12 rezagos, flujos migratorios, mes en seno y coseno, 8 unidades, ensamble de 5 redes. | F1 + F2 | RF-27 |
| 2.5 | Métricas ampliadas, comparación controlada con grupos de semillas y registro en MLflow. | F1 | RF-29, RF-41, RF-42 |
| 2.6 | Ablación con y sin variables fronterizas. | F1 | RF-44 |
| 2.7 | Diseño PCAM detallado (partición y comunicación) de cada etapa, como ADR. | F2 | OE2 |
| 2.8 | Autenticación, roles, aislamiento por comercio; tabla de trabajos y worker. | F3 | RF-62 a RF-64 |

**Criterios de salida:**
- Tabla comparativa sobre los datos públicos con al menos 3 grupos de semillas.
- La LSTM reproduce el piloto (MAPE entre 3,6 % y 4,1 %) o se documenta la causa de la diferencia (paso de numpy a PyTorch).
- Cualquier experimento se vuelve a ejecutar con un comando y su archivo YAML.

**Entregables:** `notebooks/02_seleccion_modelos_OE2.ipynb`, ADR de diseño PCAM. Versión `v0.2`.

### Fase 3 — Construcción del sistema paralelo (Sprints 3 y 4, semanas 4 y 5) → OE3

**Objetivo:** construir las versiones OpenMP, MPI y CUDA, verificar que dan los mismos resultados que la secuencial y medir su rendimiento.

**Sprint 3 — OpenMP y MPI**

| # | Actividad | Requerimientos |
|---|---|---|
| 3.1 | Formalizar la versión secuencial de referencia y el arnés de medición (tiempos, repeticiones, hardware). | RF-34, RF-40 |
| 3.2 | Núcleos C++ con OpenMP para variables y métricas sobre la matriz T×N, con respaldo en NumPy. | RF-35 |
| 3.3 | MPI con mpi4py para repartir orígenes de validación, semillas y series; reunión en el proceso raíz. | RF-36 |
| 3.4 | Estrategia de ejecución configurable. | RF-38 |
| 3.5 | Pruebas de equivalencia paralelo ≡ secuencial en la integración continua (MPI con `mpiexec -n 2`). | RF-39 |

**Sprint 4 — CUDA y campaña de medición**

| # | Actividad | Requerimientos |
|---|---|---|
| 3.6 | Entrenamiento de la LSTM en GPU por lotes y de muchas series a la vez; respaldo automático a CPU. | RF-37, RNF-13 |
| 3.7 | Combinación MPI + CUDA: cada proceso entrena su grupo de series o semillas en GPU. | RF-36, RF-37 |
| 3.8 | Búsqueda de hiperparámetros distribuida (si el tiempo lo permite). | RF-31 |
| 3.9 | Campaña de medición: procesos *p* ∈ {1, 2, 4, más nodos si el laboratorio lo permite}; hilos *h* ∈ {1, 2, 4, 8}; GPU frente a CPU; tamaños de 100 a 1.000 series; al menos 5 repeticiones. Ajuste de la ley de Amdahl. | RF-40, RNF-03 a RNF-05 |

**Criterios de salida:**
- Tablas y gráficas de tiempo, *S(p)*, *E(p)* y *f* estimada para cada tecnología.
- Pruebas de equivalencia en verde.
- RNF-03, RNF-04 y RNF-05 medidos y reportados, se cumplan o no.

**Entregables:** `notebooks/03_rendimiento_paralelo_OE3.ipynb`, insumos para el capítulo de Desarrollo (alcance del OE3). Versiones `v0.3` y `v0.4`.

### Fase 4 — Plataforma: API, inventario y dashboard (Sprints 2 a 5, frente F3)

**Objetivo:** que el comerciante y el analista usen el sistema de extremo a extremo desde la web.

| Sprint | Actividades | Requerimientos |
|---|---|---|
| 2 | Autenticación, roles y aislamiento por comercio; modelos completos de base de datos; cola de trabajos y worker; endpoints de series y pronósticos. | RF-62 a RF-64, RF-66 |
| 3 | Módulo de inventario en Python (stock de seguridad desde el error del pronóstico, punto de reorden, pedido sugerido, riesgo) y sus endpoints. Vistas: panel principal, pronósticos y datos. | RF-46 a RF-49, RF-53, RF-54, RF-59 |
| 4 | Vistas de patrones, modelos, rendimiento, inventario y recomendaciones; transparencia del pronóstico; exportación; simulador de escenarios. | RF-51, RF-55 a RF-58, RF-60, RF-61 |
| 5 | Auditoría; endurecimiento de seguridad; accesibilidad; tiempos de respuesta. | RF-65, RNF-06, RNF-10, RNF-15 a RNF-18 |

**Criterio de salida:** flujo completo funcionando y cubierto por una prueba E2E: el comerciante inicia sesión → carga sus datos → el analista entrena (trabajo en segundo plano) → publica el modelo con su ficha → el comerciante ve el pronóstico con intervalos y la recomendación de compra.

### Fase 5 — Evaluación y validación (Sprint 5, semana 6) → OE4

**Objetivo:** validar el sistema con las condiciones experimentales de la Tabla 2 y medir la mejora en la gestión de inventarios.

| # | Actividad | Requerimientos |
|---|---|---|
| 5.1 | Congelar versión de datos y de código (`v0.9`). | RNF-27 |
| 5.2 | Campaña final de experimentos: mismos datos, particiones, semillas, al menos 5 repeticiones y mismo hardware para todos los modelos. | RF-42 |
| 5.3 | Con datos de comercios si se obtuvieron; si no, validación con las series regionales y con datos sintéticos declarados como tales. | RF-06, R1 |
| 5.4 | Pruebas de significancia entre modelos. | RF-43 |
| 5.5 | Simulación retrospectiva de inventario: nivel de servicio, quiebres de stock, inventario promedio, rotación y costo frente a la política empírica o ingenua. | RF-50 |
| 5.6 | Prueba de usabilidad con 3 a 5 comerciantes (tareas y cuestionario SUS). | RNF-11 |
| 5.7 | Matriz de cumplimiento: cada RF y RNF con su prueba o evidencia. | Todos |
| 5.8 | Informe de validación exportable. | RF-45 |

**Criterio de salida:** informe de validación con todas sus cifras regenerables con un comando (RNF-28) y matriz de cumplimiento completa.

**Entregables:** `notebooks/04_validacion_OE4.ipynb`, informe de validación, matriz de cumplimiento.

### Fase 6 — Despliegue, documentación y cierre (Sprint 6, semana 7)

**Objetivo:** entregar el sistema instalable, documentado y listo para su adopción.

| # | Actividad | Requerimientos |
|---|---|---|
| 6.1 | Despliegue con Docker Compose y procedimiento de respaldo y restauración probado. | RNF-08, RNF-14 |
| 6.2 | README, guía de instalación, guía de usuario, guía de configuración HPC y fichas de los modelos. | RNF-20, RNF-26 |
| 6.3 | Guía de adopción para MIPYMES (requisitos, costos, pasos, recomendaciones). | PE |
| 6.4 | Inventario de licencias de dependencias. | RNF-22 |
| 6.5 | Insumos para los capítulos 7 (Desarrollo) y 8 (Conclusiones) de la monografía. | OE1 a OE4 |
| 6.6 | Demostración final (Sprint Review de cierre) y versión `v1.0`. | — |

**Criterio de salida:** una persona que no participó en el desarrollo instala y usa el sistema siguiendo solo el README.

---

## 6. Cronograma

### 6.1 Plan base (7 semanas)

| Semana | Sprint | F1 Datos y modelos | F2 Cómputo paralelo | F3 Plataforma | Hito |
|---|---|---|---|---|---|
| 1 | S0 | Migrar módulos del prototipo A; cuaderno piloto | *Spike* HPC: WSL2, OpenMPI, pybind11, GPU | Estructura, CI, Docker, base de API y frontend | `v0.0` Cimientos |
| 2 | S1 | Ingesta pública, calendario, EDA (OE1) | Generador sintético escalable | Esquema de BD, carga de datos, anonimización | `v0.1` OE1 reproducido |
| 3 | S2 | Variables, origen móvil, SARIMA, Prophet, LSTM en CPU | Diseño PCAM; apoyo en LSTM | Autenticación, roles, trabajos, API de pronósticos | `v0.2` OE2 reproducido |
| 4 | S3 | Ablación; ajuste de modelos | OpenMP y MPI; equivalencia | Inventario; vistas principales | `v0.3` |
| 5 | S4 | Simulación de inventario | CUDA, MPI + CUDA, campaña de medición | Vistas de análisis, transparencia, escenarios | `v0.4` OE3 medido |
| 6 | S5 | Campaña final y significancia | Medición final | Seguridad, auditoría, prueba de usabilidad | `v0.9` OE4 validado |
| 7 | S6 | Fichas de modelos e insumos de la monografía | Guía HPC | Despliegue, guías, demostración | `v1.0` Entrega |

### 6.2 Ruta crítica

`Spike HPC (S0)` → `Panel T×N y LSTM en CPU (S2)` → `MPI y CUDA (S3–S4)` → `Campaña de medición (S4)` → `Validación (S5)`.
Un retraso en el acceso a GPU retrasa directamente el OE3: por eso el *spike* va en la primera semana.

---

## 7. Product Backlog inicial

### 7.1 Épicas

| Épica | Nombre | Requerimientos | Fase |
|---|---|---|---|
| EP-01 | Cimientos y arquitectura | RNF-08, RNF-22 a RNF-27 | 0 |
| EP-02 | Datos públicos y patrones de consumo | RF-01 a RF-05, RF-07, RF-11, RF-18 a RF-23 | 1 |
| EP-03 | Datos de comercios y privacidad | RF-06, RF-08, RF-09, RF-59, RF-63 | 1 |
| EP-04 | Preparación y variables | RF-12 a RF-17 | 2 |
| EP-05 | Modelos y experimentos | RF-24 a RF-33, RF-41 a RF-44 | 2, 5 |
| EP-06 | Cómputo paralelo | RF-34 a RF-40 | 3 |
| EP-07 | Inventario | RF-46 a RF-52 | 4, 5 |
| EP-08 | API y operación | RF-62 a RF-66 | 4 |
| EP-09 | Dashboard | RF-53 a RF-61 | 4 |
| EP-10 | Validación y cierre | RF-45, RF-50, RNF-11, RNF-26 | 5, 6 |

### 7.2 Historias de los Sprints 0 y 1

Estimación en puntos de historia (escala de Fibonacci).

| ID | Historia | Criterio de aceptación | Pts | Traza |
|---|---|---|---|---|
| HU-01 | Como equipo, quiero la estructura de `Codigo Fuente/` con herramientas configuradas, para trabajar con las mismas reglas. | Estructura de la sección 10 de la arquitectura creada; `ruff`, `mypy`, `pytest` y `npm run lint` ejecutan sin errores. | 5 | EP-01 |
| HU-02 | Como equipo, quiero integración continua en cada *pull request*, para no romper lo que funciona. | El flujo de GitHub Actions corre lint, tipos, pruebas y compilación; bloquea la fusión si falla. | 3 | RNF-24 |
| HU-03 | Como analista, quiero las métricas, el origen móvil y la línea base del prototipo como paquete probado, para construir sobre ellos. | Módulos migrados con pruebas; cobertura ≥ 90 % en esos módulos; resultados idénticos al prototipo con la misma semilla. | 5 | RF-16, RF-24, RF-41 |
| HU-04 | Como equipo, quiero levantar la base de datos, la API y el frontend con un comando, para tener el mismo entorno. | `docker compose up` deja `/health` en 200 y el frontend cargando. | 5 | RNF-08 |
| HU-05 | Como integrante de HPC, quiero comprobar MPI, OpenMP y CUDA en nuestro hardware, para no descubrir bloqueos tarde. | Documento del *spike* con `mpiexec -n 4` funcionando, un núcleo OpenMP compilado y PyTorch usando la GPU elegida. | 8 | RF-35 a RF-37 |
| HU-06 | Como analista, quiero descargar y versionar la EMC, el IPC y los flujos de Migración, para reproducir el OE1. | Cada fuente se descarga con un comando; manifiesto con hash; número de meses igual al de la Tabla IV del informe. | 8 | RF-01 a RF-03, RF-11 |
| HU-07 | Como analista, quiero el calendario de eventos de frontera y festivos, para usarlos como variables y marcas. | Archivo YAML con eventos y fuentes; función que devuelve variables por fecha. | 3 | RF-05 |
| HU-08 | Como investigador, quiero regenerar las figuras y tablas del OE1 desde código, para que la evidencia sea verificable. | `make reproduce-oe1` produce las Figuras 1 a 5 y las Tablas III y IV; cifras clave coinciden (4,2 % anual, +28,8 % en diciembre, +0,72 puntos, rezago de 1 mes). | 8 | RF-18 a RF-21, RF-23 |
| HU-09 | Como comerciante, quiero cargar mis ventas en una plantilla de Excel, para recibir pronósticos de mis productos. | La carga valida la plantilla, explica errores y guarda los datos anonimizados y versionados. | 8 | RF-06, RF-07, RF-08 |
| HU-10 | Como integrante de HPC, quiero generar datos sintéticos de hasta 1.000 series, para medir la escalabilidad. | Generación con semilla fija; etiqueta de origen sintético; más de un millón de filas en menos de 2 minutos. | 3 | RF-10 |

---

## 8. Variante comprimida (4 semanas)

Si la fecha de entrega no permite 7 semanas, se aplica esta variante. Se conservan todos los requerimientos *Must* y se aplazan los *Should* y *Could*.

| Semana | Contenido |
|---|---|
| 1 | Fase 0 reducida (estructura, CI, migración del prototipo A, *spike* HPC) + ingesta pública y reproducción del OE1. |
| 2 | SARIMA, Prophet y LSTM en CPU con origen móvil; API básica con autenticación y trabajos. |
| 3 | OpenMP, MPI y CUDA (en GPU remota si no hay local) con equivalencia y medición; vistas de pronóstico e inventario. |
| 4 | Validación (OE4), informe, despliegue con Docker Compose y documentación. |

**Se aplazan:** RF-04, RF-09, RF-17, RF-22, RF-31, RF-32, RF-33, RF-43, RF-51, RF-52, RF-60, RF-65 y la prueba de usabilidad completa (RNF-11).

---

## 9. Gestión de la calidad

### 9.1 Estrategia de pruebas

| Nivel | Qué verifica | Herramienta | Dónde corre |
|---|---|---|---|
| Unitarias | Funciones del núcleo, servicios y componentes | pytest, Vitest | CI |
| Propiedades | Invariantes de métricas y particiones (p. ej., ninguna fecha de prueba en el entrenamiento) | hypothesis | CI |
| Integración | API con base de datos de prueba; permisos por rol y comercio | pytest + PostgreSQL de prueba | CI |
| Equivalencia | Paralelo ≡ secuencial | pytest + `mpiexec -n 2` | CI (MPI); local o remoto (CUDA) |
| Regresión de modelos | Las métricas sobre un conjunto fijo no empeoran más allá de una tolerancia y siempre superan la línea base | pytest | CI (datos pequeños) |
| Extremo a extremo | Flujo de inicio de sesión → pronóstico → recomendación | Playwright | CI (antes de cada versión) |
| Rendimiento | Tiempos y aceleración | `forecast_core.pipelines.benchmark` | Manual, en hardware controlado |
| Usabilidad | Tareas con comerciantes y SUS | Protocolo de prueba | Sprint 5 |

### 9.2 Revisión de código

Cada *pull request* lo revisa un integrante de otro frente con esta lista de chequeo:

- [ ] La historia está trazada a RF o RNF.
- [ ] Hay pruebas y la integración continua está en verde.
- [ ] No hay valores quemados, secretos ni datos de comercios.
- [ ] Ninguna cifra en la interfaz o en documentos carece de una ejecución registrada que la respalde.
- [ ] Se actualizó la documentación correspondiente.

### 9.3 Indicadores de calidad

| Indicador | Meta |
|---|---|
| Cobertura de pruebas del núcleo analítico | ≥ 80 % |
| Cobertura de pruebas de la API | ≥ 60 % |
| *Pull requests* con integración continua en verde al fusionar | 100 % |
| Requerimientos *Must* con prueba o evidencia | 100 % al cierre |
| Defectos críticos abiertos al cierre de cada sprint | 0 |

---

## 10. Gestión de riesgos

Probabilidad (P) e impacto (I): Alta, Media, Baja.

| ID | Riesgo | P | I | Mitigación | Disparador |
|---|---|---|---|---|---|
| R1 | No se obtienen datos transaccionales de comercios a tiempo. | A | A | Iniciar la gestión en el Sprint 1 con formato de autorización; validar con series regionales y sintéticas declaradas; documentarlo como limitación (ya reconocida en el informe). | Sin datos al final del Sprint 3. |
| R2 | No hay GPU NVIDIA disponible (el equipo revisado no tiene). | A | A | *Spike* en el Sprint 0; opciones: equipo de otro integrante, laboratorio de la universidad, Colab o Kaggle con `infra/gpu_remota/`; respaldo a CPU. | Sin GPU confirmada al cierre del Sprint 0. |
| R3 | Problemas de MPI o compilación en Windows (incluida la ruta con espacio "Codigo Fuente"). | M | M | Desarrollar HPC en WSL2 Ubuntu con OpenMPI; CI en Linux; rutas siempre entre comillas; renombrar la carpeta si persiste. | Fallas de compilación repetidas. |
| R4 | La LSTM no supera a los modelos estadísticos en series cortas o intermitentes por producto. | M | M | Mantener SARIMA, Prophet y líneas base; reportar el resultado con honestidad (es un hallazgo válido); probar híbridos si hay tiempo. | Resultados del Sprint 2. |
| R5 | La aceleración paralela es baja con datos pequeños (sobrecosto de comunicación). | A | M | Medir con datos sintéticos grandes; aglomerar tareas; análisis de Amdahl; reportar el punto de equilibrio. | *E(p)* < 0,5 en el Sprint 3. |
| R6 | El alcance excede el tiempo disponible. | M | A | Priorización MoSCoW; variante comprimida; incremento funcional cada semana. | Velocidad del Sprint 1 menor al 70 % de lo planeado. |
| R7 | Cifras fabricadas del prototipo llegan a la monografía o a la presentación. | M | A | Descartar el motor y el *seed* del prototipo B; regla "ninguna cifra sin origen" en la revisión de código. | Cualquier cifra sin ID de ejecución. |
| R8 | Curva de aprendizaje de CUDA, MPI o Next.js. | M | M | *Spikes* tempranos; programación en parejas; revisión cruzada entre frentes. | Historias bloqueadas más de 2 días. |
| R9 | Incompatibilidades entre versiones recientes (Next.js 16, Prophet y cmdstan en Windows, CUDA y PyTorch). | M | M | Versiones fijas en archivos de bloqueo; contenedores Docker; actualizar solo al inicio de un sprint. | Fallos de instalación. |
| R10 | Exposición de datos de comercios. | B | A | Anonimización en la ingesta; `data/` fuera de Git; control de acceso por comercio; auditoría. | Cualquier dato privado detectado en el repositorio. |

---

## 11. Gestión de la configuración

- **Repositorio único** con `Codigo Fuente/`, `Documentacion/`, `Documentacion Tecnica/` y `Prototipo/` (solo lectura).
- **Ramas:** `main` protegida (requiere *pull request*, una aprobación y CI en verde); ramas cortas `feat/RF-xx-…`, `fix/…`, `exp/…`, `docs/…`.
- **Commits:** Conventional Commits.
- **Versiones:** una etiqueta por sprint (`v0.0` a `v1.0`).
- **Datos:** manifiesto con hash en Git; archivos de datos fuera de Git; datos de comercios solo en almacenamiento local cifrado del equipo.
- **Modelos y experimentos:** MLflow más la tabla `modelo_publicado`; cada modelo publicado referencia su ejecución, su commit y su versión de datos.

## 12. Comunicación y seguimiento

| Mecanismo | Frecuencia | Contenido |
|---|---|---|
| Tablero de GitHub Projects | Continuo | Estado de cada historia |
| Daily Standup | Diario | Avance y bloqueos |
| Sprint Review con el director | Semanal | Demostración y aceptación |
| Reporte de estado (una página) | Semanal | Avance, indicadores, riesgos activos y decisiones |
| ADR | Cuando se decide algo relevante | Contexto, decisión y consecuencias |

**Indicadores de seguimiento del proyecto:** porcentaje de requerimientos *Must* completados, velocidad por sprint, burndown, estado de riesgos, y los indicadores técnicos clave: MAPE frente a la línea base y aceleración *S(p)*.

---

## 13. Entregables y correspondencia con la monografía

| Fase | Entregable | Objetivo | Capítulo de la monografía |
|---|---|---|---|
| 0 | Arquitectura, ADR, estructura de `Codigo Fuente/` | — | 6 (Metodología del desarrollo) |
| 1 | Pipeline de ingesta, reporte de calidad, cuaderno de patrones | OE1 | 7 (Desarrollo, alcance OE1) |
| 2 | Modelos secuenciales, comparación, diseño PCAM | OE2 | 7 (Desarrollo, alcance OE2) |
| 3 | Sistema paralelo, pruebas de equivalencia, mediciones de rendimiento | OE3 | 7 (Desarrollo, alcance OE3) |
| 4 | API, inventario y dashboard | OG, OE3 | 7 (Desarrollo, alcance OE3) |
| 5 | Informe de validación y matriz de cumplimiento | OE4 | 7 (Desarrollo, alcance OE4) y 8 (Conclusiones) |
| 6 | Sistema desplegado, guías y versión `v1.0` | OG | 8 (Conclusiones y recomendaciones) |

## 14. Próximos pasos

1. Revisar en equipo los cuatro documentos de `Documentacion Tecnica/` y ajustar lo que haga falta.
2. Fijar la fecha de entrega y elegir entre el plan base y la variante comprimida.
3. Asignar los frentes F1, F2 y F3 y el primer Scrum Master.
4. Confirmar de dónde saldrá la GPU para CUDA.
5. Iniciar la Fase 0: crear la estructura de `Codigo Fuente/`.
