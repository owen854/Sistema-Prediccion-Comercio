# Evaluación de Viabilidad del Prototipo

**Proyecto:** Sistema de Predicción de Demanda para el Comercio Minorista Fronterizo
**Versión:** 1.0 — 16/11/2026
**Alcance:** carpeta `Prototipo/` (dos subproyectos) frente a la documentación del proyecto y a los requerimientos de `01_Requerimientos_RF_RNF.md`.

---

## 1. Resumen ejecutivo

**Decisión recomendada: avanzar de forma selectiva.** El prototipo no se continúa tal como está, pero tampoco se descarta completo:

| Subproyecto | Veredicto | Qué se hace |
|---|---|---|
| **A. `demand-forecast-hpc`** (Python) | **Viable como semilla del núcleo analítico.** Puntaje 3,3 / 5. | Se migran y amplían sus módulos (métricas, origen móvil, línea base, carga de datos, generador sintético) dentro de la nueva arquitectura, con pruebas. |
| **B. `retail-demand-prediction-system`** (Next.js + PostgreSQL) | **No viable como sistema; útil como base visual.** Puntaje 1,7 / 5. | Se reutilizan el diseño visual, la estructura de la interfaz y las ideas de inventario. Se descartan su "motor de predicción", sus datos semilla, sus métricas y su acceso directo a la base de datos. |

**Tecnologías:** el frontend del prototipo (Next.js, React, TypeScript y Tailwind CSS) **sí se integra bien con un backend en Python**, siempre que Next.js se use solo como capa de presentación y consuma una API en **FastAPI**. Se recomienda mantener esas tecnologías de frontend (sección 6).

> **Alerta de integridad académica.** El prototipo B muestra cifras que ningún modelo calcula: una tabla de comparación con un "ARIMAX Fronterizo" con MAPE de 5,84 %, R² = 0,914, una reducción de quiebres de stock de 41 % y datos fronterizos y cambiarios fijos en el código. Además, contradicen el informe de OE1/OE2, que seleccionó la LSTM y descartó ARIMA. **Ninguna de esas cifras debe aparecer en la monografía, en presentaciones ni en el sistema final.** Detalle en la sección 4.2.

---

## 2. Inventario de lo revisado

### 2.1 Subproyecto A — `demand-forecast-hpc`

| Elemento | Contenido |
|---|---|
| Lenguaje | Python 3.10+ (numpy, pandas, scipy, scikit-learn, matplotlib) |
| Estado declarado | Etapa 1 de 5 terminada (datos, EDA, RMSE/MAPE, origen móvil, línea base, pronóstico a futuro) |
| Módulos | `src/metrics.py`, `src/validation.py`, `src/baselines.py`, `src/data_loader.py`, `src/data_generation.py` |
| Scripts | `scripts/00_download_real_data.py` (TRM real desde datos.gov.co), `scripts/01_eda_and_baseline.py` (Etapa 1) |
| Datos | Ventas sintéticas: 60 SKU × 1.406 días (84.360 filas) y exógenas sintéticas diarias |
| Resultados | Línea base ingenua estacional con 6 orígenes móviles: MAPE entre 14,4 % y 17,2 % sobre datos sintéticos |

### 2.2 Subproyecto B — `retail-demand-prediction-system`

| Elemento | Contenido |
|---|---|
| Stack | Next.js 16.2, React 19.2, TypeScript 5.9, Tailwind CSS 4, Drizzle ORM 0.45, PostgreSQL (driver `pg`) |
| Interfaz | Tres pestañas: tablero con simulador "qué pasaría si", catálogo de SKU con riesgo de quiebre, y panel de metodología; esquema del corredor fronterizo; gráfica de demanda en SVG propio |
| Backend | Rutas de API de Next.js (`/api/forecast`, `/api/skus`, `/api/health`) con acceso directo a PostgreSQL |
| Datos | Tablas `skus`, `historical_demand_series`, `border_bridges`, `simulation_scenarios`, `restock_orders`, pobladas por un *seed* con valores inventados |
| "Motor de predicción" | `src/lib/forecast-engine.ts`: multiplicadores deterministas con elasticidades fijas |
| Ausentes | README, archivo de bloqueo de dependencias, `.env.example`, migraciones, pruebas |

---

## 3. Hallazgos del subproyecto A (Python)

### 3.1 Fortalezas

1. **Alineación metodológica correcta.** Implementa lo que exige la Tabla 2 del documento: métricas RMSE y MAPE con la fórmula de Hyndman y Koehler, validación con origen móvil sin fuga de información y línea base ingenua estacional ([validation.py](../Prototipo/demand-forecast-hpc/demand-forecast-hpc/src/validation.py), [metrics.py](../Prototipo/demand-forecast-hpc/demand-forecast-hpc/src/metrics.py)).
2. **Diseño pensado para el paralelismo.** La matriz *T días × N series* ([data_loader.py:26](../Prototipo/demand-forecast-hpc/demand-forecast-hpc/src/data_loader.py#L26)) es exactamente la partición que necesitan OpenMP, MPI y CUDA.
3. **Honestidad metodológica.** Los datos sintéticos están declarados como tales en el código y en el README, y el MAPE informa cuántos ceros excluye en lugar de ocultarlos.
4. **Una fuente real ya integrada.** Descarga la TRM de datos.gov.co con la API Socrata.
5. **Código legible**, con docstrings que citan la documentación del proyecto.

### 3.2 Debilidades

| # | Hallazgo | Impacto | Corrección propuesta |
|---|---|---|---|
| A1 | Solo cubre la Etapa 1: no hay SARIMA, Prophet, LSTM, OpenMP, MPI, CUDA, API ni interfaz. | Avance aproximado de 15 % del sistema. | Plan por fases (`04_Plan_Gestion_Proyecto.md`). |
| A2 | **No reproduce el trabajo del informe.** Usa ventas sintéticas diarias por SKU, mientras que el informe usa la EMC, el IPC de Cúcuta y Migración Colombia en frecuencia mensual. El cuaderno de Colab del piloto LSTM no está en el repositorio. | Las evidencias del OE1 y OE2 no se pueden regenerar desde el código. | Incorporar el cuaderno del piloto y crear ingestores para las tres fuentes públicas (RF-01 a RF-03). |
| A3 | Las exógenas sintéticas (aforo diario, diferencial cambiario VES) no tienen fuente pública diaria; el diferencial cambiario no aparece en el documento. | Variables no justificables ante la Circular SIC 002/2024. | Mantenerlas solo en el generador sintético; las exógenas reales serán flujos migratorios, IPC, TRM y eventos. |
| A4 | Fecha final por defecto = "ayer" ([01_eda_and_baseline.py:44](../Prototipo/demand-forecast-hpc/demand-forecast-hpc/scripts/01_eda_and_baseline.py#L44)). | El mismo comando produce datos y métricas distintas cada día; rompe la reproducibilidad. | Fechas fijas en archivos de configuración. |
| A5 | Dependencias sin versión fija en `requirements.txt`; importaciones con `sys.path.insert` ([línea 26](../Prototipo/demand-forecast-hpc/demand-forecast-hpc/scripts/01_eda_and_baseline.py#L26)). | Entorno no reproducible; paquete no instalable. | `pyproject.toml` con archivo de bloqueo; paquete instalable. |
| A6 | Sin pruebas automatizadas. | No hay garantía al refactorizar ni al paralelizar. | Pruebas unitarias y de equivalencia (RF-39). |
| A7 | `to_matrix` rellena con 0 los días sin registro ([data_loader.py:34](../Prototipo/demand-forecast-hpc/demand-forecast-hpc/src/data_loader.py#L34)). | Confunde "no hubo venta" con "no hay dato" (tienda cerrada o registro faltante). | Regla configurable y marcada en el reporte de calidad. |
| A8 | El reporte de calidad no revisa duplicados ni huecos; la línea base solo admite periodo 7. | Insuficiente para datos reales y series mensuales. | Ampliar según RF-07 y RF-24. |
| A9 | Los datos sintéticos generados (≈ 3,2 MB) están versionados en el repositorio. | Crecimiento innecesario del repositorio. | Regenerarlos con semilla fija y excluirlos con `.gitignore`. |

---

## 4. Hallazgos del subproyecto B (Next.js)

### 4.1 Fortalezas

1. **Interfaz cuidada y contextualizada.** Lenguaje y ejemplos de la región (La Parada, Cenabastos, puentes internacionales), tipografía y paleta consistentes, diseño profesional.
2. **Buenas ideas de producto que sí corresponden al objetivo general:** clasificación de riesgo de quiebre (crítico, preventivo, óptimo), días de cobertura, punto de reorden, cantidad sugerida de pedido, simulador de escenarios y órdenes de reabastecimiento. Corresponden a RF-47 a RF-52.
3. **Stack moderno y con buen soporte**, fácil de conectar a una API en Python.
4. El modelo de datos (`skus`, `restock_orders`) es un punto de partida razonable para el módulo de inventario.

### 4.2 Debilidades críticas

| # | Hallazgo | Evidencia | Impacto |
|---|---|---|---|
| B1 | **No hay modelo de predicción.** El "modelo ARIMAX Fronterizo" es una suma de multiplicadores con elasticidades fijas y límites arbitrarios (0,22 a 2,65). | [forecast-engine.ts:60](../Prototipo/retail-demand-prediction-system/src/lib/forecast-engine.ts#L60) | No cumple OE2, OE3 ni OE4. |
| B2 | **Métricas fabricadas.** R² fijo en 0,914; el MAPE mostrado es el promedio de un campo `mapeScore` escrito a mano en el *seed* (y 5,8 fijo para todo SKU nuevo). | [forecast-engine.ts:368](../Prototipo/retail-demand-prediction-system/src/lib/forecast-engine.ts#L368), [forecast-engine.ts:335](../Prototipo/retail-demand-prediction-system/src/lib/forecast-engine.ts#L335), [skus/route.ts:118](../Prototipo/retail-demand-prediction-system/src/app/api/skus/route.ts#L118) | Riesgo de integridad académica. |
| B3 | **Tabla de comparación de modelos inventada** (SMA 18,42 %, Holt-Winters 12,15 %, ARIMA 9,64 %, ARIMAX 5,84 %) y conclusión de "41 % menos quiebres". Contradice el informe (LSTM seleccionada; ARIMA descartado). | [ProjectMethodologyPanel.tsx:203](../Prototipo/retail-demand-prediction-system/src/components/ProjectMethodologyPanel.tsx#L203), [línea 215](../Prototipo/retail-demand-prediction-system/src/components/ProjectMethodologyPanel.tsx#L215) | Riesgo de integridad académica; incoherencia con la documentación. |
| B4 | **Datos históricos simulados con funciones seno y coseno.** Solo 60 días anclados al 15/05/2025; las ventas "reales" se derivan del propio pronóstico más una onda, por lo que el error está fijado de antemano. | [seed.ts:243](../Prototipo/retail-demand-prediction-system/src/db/seed.ts#L243), [seed.ts:303](../Prototipo/retail-demand-prediction-system/src/db/seed.ts#L303) | Cualquier métrica calculada sobre ellos es circular. |
| B5 | **Datos de contexto fijos y sin fuente:** TRM, tasas del bolívar, aforos y tiempos de espera de los puentes. | [page.tsx:35](../Prototipo/retail-demand-prediction-system/src/app/page.tsx#L35), [forecast/route.ts:39](../Prototipo/retail-demand-prediction-system/src/app/api/forecast/route.ts#L39) | Se presentan como reales sin serlo. |
| B6 | **El modelo de datos no admite historia por producto:** `historical_demand_series` no tiene producto ni comercio y guarda la fecha como texto. | [schema.ts:36](../Prototipo/retail-demand-prediction-system/src/db/schema.ts#L36) | Imposible pronosticar por SKU, que es la unidad de análisis del documento. |
| B7 | **Lógica de negocio en el navegador.** Los cálculos de inventario corren en el cliente y la API guarda los ingresos proyectados que envía el cliente sin recalcularlos. | [forecast/route.ts:102](../Prototipo/retail-demand-prediction-system/src/app/api/forecast/route.ts#L102) | Resultados manipulables; lógica no reutilizable desde Python. |
| B8 | **Seguridad:** sin autenticación ni roles, sin validación de esquemas en las rutas, credenciales en `drizzle.config.json`. | `src/app/api/*`, `drizzle.config.json` | Incumple RNF-15 a RNF-17. |
| B9 | **Mantenibilidad:** componente de 1.540 líneas, gráfica SVG hecha a mano, *seed* ejecutado en cada petición, sin pruebas, sin README ni archivo de bloqueo. Nació de una plantilla genérica (`nextjs-postgresql-template`, `__arenaNextJsPostgresqlPool`). | [FronteraForecastDashboard.tsx](../Prototipo/retail-demand-prediction-system/src/components/FronteraForecastDashboard.tsx), [package.json:2](../Prototipo/retail-demand-prediction-system/package.json#L2), [db/index.ts:15](../Prototipo/retail-demand-prediction-system/src/db/index.ts#L15) | Costo alto de evolución; instalación no reproducible. |
| B10 | Variables no previstas en el documento (diferencial VES, remesas, elasticidades por puente) y lenguaje técnico ("ARIMAX", "elasticidad", "factor Z") poco adecuado para un comerciante. | Interfaz | Desalineación con el documento y con RNF-10. |

---

## 5. Matriz de evaluación ponderada

Escala de 1 (muy deficiente) a 5 (excelente). El puntaje ponderado es la suma de peso × calificación dividida entre 100.

| # | Criterio | Peso | A (Python) | B (Next.js) | Justificación |
|---|---|---|---|---|---|
| C1 | Alineación con los objetivos OE1–OE4 | 20 % | 3 | 2 | A cubre parte del OE1 y la base del OE2. B solo cubre la visualización y el inventario del OG. |
| C2 | Validez del motor de predicción y de las métricas | 20 % | 4 | 1 | A calcula métricas correctas con origen móvil. B no tiene modelo y sus métricas son fijas. |
| C3 | Arquitectura, modularidad y mantenibilidad | 10 % | 3 | 2 | A es modular pero no es paquete ni tiene pruebas. B mezcla presentación, negocio y datos. |
| C4 | Preparación para el cómputo paralelo (PCAM) | 10 % | 3 | 1 | A diseñó la matriz T×N para particionar. B no contempla paralelismo. |
| C5 | Integración con el stack Python | 10 % | 5 | 2 | A es Python. B duplica el backend en TypeScript; solo su capa visual se integra bien. |
| C6 | Trazabilidad y honestidad de los datos | 10 % | 5 | 1 | A declara lo sintético. B presenta datos inventados como reales. |
| C7 | Usabilidad y valor para la MIPYME | 10 % | 1 | 4 | A no tiene interfaz. B tiene una interfaz rica, aunque con jerga técnica. |
| C8 | Seguridad, privacidad y cumplimiento legal | 5 % | 2 | 1 | Ninguno maneja anonimización; B además expone endpoints sin control de acceso. |
| C9 | Pruebas, documentación y entorno reproducible | 5 % | 2 | 1 | A tiene un buen README pero no pruebas ni versiones fijas. B no tiene nada de eso. |
| | **Puntaje ponderado (sobre 5)** | **100 %** | **3,3** | **1,7** | |

**Umbral de decisión:** ≥ 3,5 continuar tal cual; 2,5 a 3,5 continuar con refactorización; < 2,5 no continuar como base técnica. A queda en "continuar con refactorización" y B en "no continuar como base técnica", aunque su capa visual sí se aprovecha.

---

## 6. ¿El frontend del prototipo se integra bien con Python?

Se compararon cuatro alternativas para la interfaz, asumiendo un backend en Python:

| Criterio | **Next.js + FastAPI** (recomendada) | Streamlit | Plotly Dash | Power BI |
|---|---|---|---|---|
| Integración con Python | Muy buena, por API REST con contrato OpenAPI; los tipos de TypeScript se generan desde la API | Nativa | Nativa | Por conector o archivos |
| Experiencia para el comerciante (móvil, simplicidad) | Alta; control total del diseño | Media; aspecto de herramienta de análisis | Media | Media; requiere licencia para compartir |
| Autenticación, roles y varios comercios | Completa | Limitada | Limitada | Depende de licencias |
| Reutiliza el prototipo | Sí (diseño, componentes, flujo) | No | No | No |
| Costo de licencias | Ninguno | Ninguno | Ninguno | **Power BI Pro tiene costo**, contrario a la justificación práctica del documento |
| Curva de aprendizaje | Mayor (dos lenguajes) | Baja | Media | Baja |
| Escalabilidad y mantenibilidad | Alta; capas separadas | Baja con muchas vistas | Media | N/A |

**Conclusión:** se mantiene **Next.js + React + TypeScript + Tailwind CSS** como frontend, con estas condiciones:

1. Next.js **no accede a la base de datos**: se elimina Drizzle y toda consulta pasa por la API FastAPI (RNF-23).
2. Los cálculos de pronóstico e inventario se mueven a Python; el frontend solo presenta.
3. Los tipos de TypeScript se generan automáticamente desde el OpenAPI de FastAPI, para evitar desalineaciones.
4. Se actualiza Node.js a una versión LTS vigente: el equipo usa Node 20, que terminó su soporte en abril de 2026.

Streamlit queda como **plan de contingencia** si el equipo no logra sostener dos lenguajes, y como herramienta interna opcional para explorar experimentos.

---

## 7. Qué se conserva, qué se refactoriza y qué se descarta

| Elemento del prototipo | Decisión | Destino en la nueva arquitectura |
|---|---|---|
| `metrics.py` (RMSE, MAPE, exclusión de ceros) | **Conservar y ampliar** (MAE, WAPE, sMAPE, MASE) | `forecast_core/evaluation/metrics.py` |
| `validation.py` (origen móvil) | **Conservar** | `forecast_core/evaluation/backtesting.py` |
| `baselines.py` (ingenuo estacional) | **Ampliar** (periodo según frecuencia, ingenuo, media móvil) | `forecast_core/models/naive.py` |
| `data_loader.py` (matriz T×N, reporte de calidad) | **Refactorizar** (huecos, duplicados, regla de ceros) | `forecast_core/preprocessing/panel.py`, `forecast_core/validation/quality.py` |
| `data_generation.py` (generador sintético) | **Conservar con etiqueta de origen** y tamaño escalable | `forecast_core/ingestion/synthetic.py` |
| `00_download_real_data.py` (TRM) | **Conservar** | `forecast_core/ingestion/trm.py` |
| `01_eda_and_baseline.py` | **Dividir** en pipeline y cuaderno de EDA | `forecast_core/pipelines/`, `notebooks/` |
| Diseño visual, tipografías y paleta del frontend | **Conservar** | `frontend/src/app/globals.css`, componentes de interfaz |
| `FronteraForecastDashboard.tsx` | **Refactorizar** en vistas y componentes pequeños conectados a la API | `frontend/src/app/(dashboard)/…` |
| `DemandForecastChart.tsx` (SVG hecho a mano) | **Reemplazar** por una librería de gráficas (Recharts o ECharts) con intervalos | `frontend/src/components/charts/` |
| `BorderCorridorSchematic.tsx` | **Conservar** solo con datos reales (flujos de Migración Colombia) o como ilustración sin cifras | `frontend/src/components/border/` |
| Fórmulas de stock de seguridad, punto de reorden y pedido | **Reimplementar en Python** con el stock de seguridad basado en el error del pronóstico | `forecast_core/inventory/policies.py` |
| Esquema `skus` y `restock_orders` | **Rediseñar** con producto, comercio, fechas tipadas y llaves foráneas | `forecast_api/db/models/` |
| `forecast-engine.ts` (multiplicadores) | **Descartar** | Lo sustituyen los modelos reales y el simulador de RF-51 |
| `seed.ts` (datos inventados) | **Descartar** | Datos públicos reales y sintéticos etiquetados |
| Tabla de modelos y conclusiones del panel de metodología | **Descartar** | La tabla se alimenta de los experimentos registrados (RF-42) |
| Rutas de API de Next.js y Drizzle ORM | **Descartar** | API FastAPI |

---

## 8. Brechas frente a los objetivos

| Objetivo | Lo que aporta el prototipo | Lo que falta |
|---|---|---|
| **OE1** | Reporte de calidad básico y EDA sobre sintéticos (A). | Ingesta de EMC, IPC y Migración; reproducir los cuatro patrones del informe; correlación cruzada; calendario de eventos. |
| **OE2** | Métricas, origen móvil y línea base (A). | SARIMA, Prophet, LSTM; variables exógenas reales; diseño PCAM (partición y comunicación) implementado en código. |
| **OE3** | Matriz T×N lista para particionar (A). | Todo: OpenMP, MPI, CUDA, versión secuencial de referencia, pruebas de equivalencia, medición de aceleración. |
| **OE4** | Nada. | Datos de comercios (o validación regional), comparación con significancia, simulación de inventario, informe de validación. |
| **OG** | Interfaz y lógica de inventario no sustentadas en modelos (B). | Conectar inventario y dashboard a pronósticos reales con intervalos. |

**Avance estimado frente al sistema completo:** alrededor de 15 % en el núcleo analítico (A) y 30 % en el diseño de la interfaz (B), sin contar backend, paralelismo ni validación.

---

## 9. Hallazgos del entorno de desarrollo

Se revisó el equipo de desarrollo donde se hizo esta evaluación:

| Recurso | Estado | Consecuencia |
|---|---|---|
| CPU | Intel Core i5-1135G7, 4 núcleos físicos, 8 hilos, 15,7 GB de RAM | Las pruebas con MPI y OpenMP en este equipo llegan a *p* = 4 con eficiencia útil. |
| GPU | Intel Iris Xe, **sin GPU NVIDIA** | **CUDA no se puede ejecutar en este equipo.** Hay que asegurar una GPU (equipo de otro integrante, laboratorio de la universidad, Google Colab o Kaggle) en la Fase 0. |
| MPI | No instalado (ni MS-MPI ni OpenMPI) | Instalar OpenMPI en WSL2 (recomendado) o MS-MPI en Windows. |
| Compiladores | g++ 16.2 (MSYS2), sin CMake ni MSVC | Usar WSL2 con g++ y CMake para los núcleos OpenMP. |
| WSL | Ubuntu disponible | Entorno recomendado para el desarrollo de cómputo paralelo. |
| Node.js | v20.18 (fin de soporte en abril de 2026) | Actualizar a una versión LTS vigente. |
| Python | 3.12.3 | Adecuado. |
| Docker | No instalado | Necesario para el despliegue con Docker Compose; opcional en desarrollo. |

Estos hallazgos alimentan el registro de riesgos del plan de gestión (R2 y R3).
