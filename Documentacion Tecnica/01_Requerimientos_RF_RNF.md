# Especificación de Requerimientos del Sistema

**Proyecto:** Sistema de Predicción de Demanda para el Comercio Minorista Fronterizo (Norte de Santander)
**Versión:** 1.0 — 16/11/2026
**Estado:** Propuesta para revisión del equipo

---

## 1. Propósito y alcance

Este documento define los **requerimientos funcionales (RF)** y **no funcionales (RNF)** del sistema. Cada requerimiento se traza a los objetivos del documento del proyecto, para garantizar que el sistema construido permita cumplirlos y que la solución sea coherente con lo redactado.

**Objetivo general (OG):** Implementar un sistema de predicción de demanda para el comercio minorista en Norte de Santander, utilizando machine learning y cómputo paralelo, para optimizar la gestión de inventarios y las decisiones comerciales de las MIPYMES.

| Código | Objetivo específico | Fase metodológica (CRISP-DM / PCAM) |
|---|---|---|
| **OE1** | Identificar los patrones de consumo en el comercio minorista de Cúcuta y municipios, considerando la influencia del comercio transfronterizo. | Comprensión del negocio y de los datos |
| **OE2** | Seleccionar algoritmos de pronóstico (ARIMA, LSTM, Prophet) y estrategias de paralelización para el procesamiento de grandes volúmenes de datos transaccionales. | Preparación de datos y selección de técnicas; PCAM: partición y comunicación |
| **OE3** | Construir un sistema paralelo que procese datos históricos de ventas con MPI y entrene modelos de deep learning con CUDA para la predicción de demanda. | Modelado; PCAM: aglomeración y mapeo |
| **OE4** | Validar el sistema con datos de comercios locales, midiendo el error de predicción y la mejora en la gestión de inventarios. | Evaluación y despliegue |

### 1.1 Fuentes analizadas

| Documento | Aporte a los requerimientos |
|---|---|
| `Documentacion/Leal_1094047490_ProyectoDocumento (4).docx` | Objetivos, producto esperado, metodología CRISP-DM + PCAM, Tabla 2 (variables y condiciones experimentales), marco legal, herramientas (Python; C/C++ con OpenMP, MPI y CUDA). |
| `Documentacion/Informe_Evidencia_OE1_OE2_IEEE (3).docx` | Fuentes públicas reales (EMC, IPC Cúcuta, Migración Colombia), patrones de consumo hallados, selección de la LSTM, prueba piloto (MAPE 3,82 % frente a 8,43 %), Tabla VIII de paralelización, limitaciones. |
| `Documentacion/Articulo_Revision_Sistematica.docx` | Buenas prácticas de la literatura: comparar siempre con referencias estadísticas, reportar MAPE y RMSE, intervalos de incertidumbre para el inventario de seguridad, entrenar muchos modelos en GPU, pruebas de significancia, indicadores de inventario, variables fronterizas. |
| `Documentacion/mapa_revision_*.txt` | Mapa de coocurrencia (VOSviewer) que confirma el vacío: *gpu* y *lstm* en zonas de baja densidad; sin términos de frontera o MIPYME. |
| `Plan_Trabajo_CRISP_DM_Scrum.md` | Métricas de éxito comercial (MAPE < 15 %, reducir quiebres de stock), variables comerciales (promociones, festivos, quincenas), dashboard de consulta por producto y fecha. |

---

## 2. Contexto del sistema

### 2.1 Actores

| Actor | Descripción | Necesidad principal |
|---|---|---|
| **Comerciante (MIPYME)** | Dueño o administrador de un comercio minorista de Cúcuta y su área metropolitana. Recursos y conocimiento técnico limitados [5]. | Saber cuánto va a vender, qué comprar y cuándo, en lenguaje sencillo. |
| **Analista / Investigador** | Integrante del equipo que gestiona datos, entrena modelos y ejecuta experimentos. | Entrenar, comparar y validar modelos de forma reproducible; medir el rendimiento paralelo. |
| **Administrador** | Responsable de usuarios, comercios, configuración y respaldos. | Operar el sistema de forma segura. |
| **Fuentes externas** | DANE (EMC, IPC), Migración Colombia y Superfinanciera (TRM) vía datos.gov.co. | Proveer series públicas que el sistema descarga. |

### 2.2 Niveles de datos

El informe de OE1/OE2 trabajó con series públicas **mensuales y agregadas**, mientras que el objetivo final del proyecto es pronosticar la demanda **por producto o categoría y punto de venta** (unidad de análisis del documento). El sistema debe soportar ambos niveles con el mismo pipeline:

| Nivel | Datos | Frecuencia | Estado | Uso |
|---|---|---|---|---|
| **A. Regional público** | Índice de ventas reales EMC (nacional), IPC Cúcuta y nacional, entradas por puestos migratorios de Norte de Santander, TRM, eventos de frontera | Mensual (TRM diaria) | Disponible | OE1, OE2, validación regional del OE4 |
| **B. Transaccional MIPYME** | Ventas por fecha, producto, cantidad y valor; inventario, precio y promoción si existen | Diaria o semanal | Pendiente de autorización de comercios | OE4 (validación con datos locales) e inventarios |
| **S. Sintético** | Ventas simuladas por SKU con exógenas | Diaria | Disponible (generador del prototipo) | Desarrollo, pruebas y medición de escalabilidad paralela. **Siempre declarado como sintético.** |

### 2.3 Convenciones

- **Prioridad (MoSCoW):** **M** = Debe (imprescindible para cumplir los objetivos), **S** = Debería (alto valor, se hace si el tiempo lo permite), **C** = Podría (mejora opcional).
- **Trazabilidad:** OG, OE1–OE4; **PE** = producto esperado del documento; **ML** = marco legal; **T2** = Tabla 2 del documento (variables y condiciones experimentales); **RS** = recomendación de la revisión sistemática.

---

## 3. Requerimientos funcionales

### 3.1 Módulo de ingesta y gestión de datos

| ID | Requerimiento | Descripción y criterio de aceptación | Prior. | Traza |
|---|---|---|---|---|
| RF-01 | Ingesta de la EMC del DANE | Descarga o carga el anexo del índice de ventas reales (total sin otros vehículos, base 2019 = 100) y lo normaliza a una serie mensual. Debe reproducir las 164 observaciones (ene-2013 a ago-2026) del informe. | M | OE1 |
| RF-02 | Ingesta del IPC por ciudades | Carga la variación mensual del IPC de Cúcuta y nacional y reconstruye el índice (dic-2016 = 100). Reproduce las 117 observaciones del informe. | M | OE1 |
| RF-03 | Ingesta de flujos migratorios | Descarga de datos.gov.co el conjunto "Entradas de extranjeros a Colombia", filtra los 5 puestos de Norte de Santander y agrega por mes. Trata los meses sin registro (abr-2020) según una regla configurable y documentada. | M | OE1 |
| RF-04 | Ingesta de la TRM | Descarga la TRM diaria (dataset 32sa-8pi3) y la agrega a la frecuencia requerida. | S | OE1, OE2 |
| RF-05 | Calendario de eventos | Mantiene un catálogo editable de festivos de Colombia, quincenas, temporadas (diciembre) y eventos de frontera (cierres y reaperturas 2015–2022, con su fuente). | M | OE1, OE2 |
| RF-06 | Carga de datos transaccionales de MIPYMES | Permite cargar archivos CSV o Excel con una plantilla definida (fecha, código de producto, categoría, cantidad, valor, punto de venta; opcionales: precio, promoción, stock). Rechaza archivos que no cumplan la plantilla y explica por qué. | M | OE4, PE |
| RF-07 | Validación y reporte de calidad | Para cada carga genera un reporte de calidad: filas, series, cobertura temporal, nulos, duplicados, negativos, huecos, % de ceros y ajustes aplicados. El reporte queda asociado a la versión del conjunto de datos. | M | OE1 |
| RF-08 | Anonimización y seudonimización | Antes de almacenar datos transaccionales, elimina identificadores de clientes y seudonimiza el comercio y el punto de venta. Ningún dato personal de consumidores se persiste. | M | ML (Ley 1581) |
| RF-09 | Registro de autorización del comerciante | Cada conjunto de datos transaccional queda asociado a la autorización del comerciante (fecha, alcance, finalidad académica). Sin autorización registrada no se puede procesar. | S | ML (Ley 1581) |
| RF-10 | Generador de datos sintéticos | Genera ventas sintéticas por SKU con estacionalidad semanal, quincenas, diciembre, tendencia, exógenas y ruido de conteo, con tamaño configurable (series, días) y semilla fija. Todo dato sintético queda etiquetado como tal en la base de datos, los reportes y la interfaz. | M | OE3, RNF-27 |
| RF-11 | Versionado de conjuntos de datos | Cada ingesta crea una versión inmutable con fecha, fuente, hash del archivo original y reporte de calidad. Los experimentos referencian la versión exacta usada. | M | T2 |

### 3.2 Módulo de preparación de datos e ingeniería de variables

| ID | Requerimiento | Descripción y criterio de aceptación | Prior. | Traza |
|---|---|---|---|---|
| RF-12 | Limpieza configurable | Elimina duplicados, unifica formatos de fecha y códigos de producto, trata faltantes y atípicos con reglas configurables. Cada ajuste queda registrado en una bitácora de preparación. | M | OE2 |
| RF-13 | Agregación temporal y jerárquica | Agrega a frecuencia diaria, semanal o mensual y por jerarquía (producto → categoría → comercio → total). | M | OE2 |
| RF-14 | Construcción del panel de series | Construye la matriz alineada *T periodos × N series* (formato base para OpenMP, MPI y CUDA) y el periodo común entre series. Reproduce el panel de 162 meses del informe. | M | OE2, OE3 |
| RF-15 | Ingeniería de variables | Genera rezagos, medias y desviaciones móviles, variación anual del logaritmo, codificación cíclica del mes y día (seno/coseno), festivos, quincenas, eventos de frontera, flujos migratorios rezagados, brecha de inflación local y TRM. Las variables se definen por configuración. | M | OE2 |
| RF-16 | Particiones temporales y origen móvil | Define particiones de entrenamiento, validación y prueba en orden cronológico y validación con origen móvil (horizonte, paso y número de orígenes configurables). Una prueba automática verifica que no hay fuga de información futura. | M | OE2, T2 |
| RF-17 | Justificación de variables | Cada variable usada por un modelo tiene una ficha con su definición, fuente y justificación de idoneidad (correlación, aporte medido en ablación). | S | ML (Circular SIC 002/2024) |

### 3.3 Módulo de análisis exploratorio (patrones de consumo)

| ID | Requerimiento | Descripción y criterio de aceptación | Prior. | Traza |
|---|---|---|---|---|
| RF-18 | Descomposición de series | Descompone tendencia, estacionalidad y residuo (clásica multiplicativa y STL), calcula la fuerza de la estacionalidad y los índices estacionales. Reproduce el +28,8 % de diciembre y la fuerza 0,76 del informe. | M | OE1 |
| RF-19 | Crecimiento y choques | Calcula el crecimiento real anual y detecta choques (p. ej., abril de 2020). | M | OE1 |
| RF-20 | Comparación de inflación local | Compara la inflación anual de Cúcuta con la nacional y calcula la brecha (media, máxima, meses por encima). | M | OE1 |
| RF-21 | Correlación cruzada con la frontera | Calcula la correlación cruzada con rezagos entre flujos fronterizos y ventas, con bandas de significancia y opción de excluir periodos atípicos (pandemia). | M | OE1 |
| RF-22 | Detección de atípicos y eventos | Detecta y marca valores atípicos y los asocia a eventos del calendario (RF-05). | S | OE1 |
| RF-23 | Reporte reproducible de patrones | Genera las tablas y figuras de patrones de consumo desde código (sin pasos manuales), exportables a PNG y CSV. | M | OE1, RNF-28 |

### 3.4 Módulo de modelado y pronóstico

| ID | Requerimiento | Descripción y criterio de aceptación | Prior. | Traza |
|---|---|---|---|---|
| RF-24 | Modelos de referencia | Implementa pronóstico ingenuo, ingenuo estacional (periodo según frecuencia: 7, 52 o 12) y media móvil. | M | T2, OE4 |
| RF-25 | ARIMA/SARIMA/SARIMAX | Implementa ARIMA y SARIMA, con variante SARIMAX con exógenas y selección de órdenes por criterio de información (AIC). | M | OE2, T2 |
| RF-26 | Prophet | Implementa Prophet con festivos de Colombia y eventos de frontera como regresores o efectos especiales. | M | OE2, T2 |
| RF-27 | LSTM | Implementa la red LSTM en PyTorch con variables exógenas, ensamble de varias redes y semillas, e hiperparámetros configurables (ventana, unidades, capas, épocas, tasa de aprendizaje). Reproduce la configuración del piloto (12 rezagos, 8 unidades, ensamble de 5 redes, Adam). | M | OE2, OE3 |
| RF-28 | Interfaz común de modelos | Todos los modelos cumplen la misma interfaz (`fit`, `predict`, `save`, `load`) para compararse bajo las mismas condiciones. | M | T2 |
| RF-29 | Registro de modelos y experimentos | Registra por cada entrenamiento: modelo, versión, hiperparámetros, versión de datos, semilla, estrategia de ejecución, hardware, métricas y artefactos. | M | T2, RNF-25 |
| RF-30 | Pronóstico a futuro con intervalos | Genera pronósticos por serie (producto, categoría, comercio o agregado) con horizonte configurable e intervalos de predicción (p. ej., 80 % y 95 %). | M | OG, PE, RS |
| RF-31 | Búsqueda de hiperparámetros | Ejecuta búsquedas en rejilla o aleatorias, distribuibles en paralelo (RF-36). | S | OE3, RS |
| RF-32 | Reentrenamiento | Permite reentrenar bajo demanda o al cargar nuevos datos, conservando el historial de versiones. | S | OG |
| RF-33 | Modelos adicionales | Integra un modelo de *gradient boosting* (LightGBM o XGBoost) o un híbrido (ARIMA-LSTM, Prophet-XGBoost) como línea de mejora. | C | RS |

### 3.5 Módulo de cómputo paralelo (HPC)

| ID | Requerimiento | Descripción y criterio de aceptación | Prior. | Traza |
|---|---|---|---|---|
| RF-34 | Versión secuencial de referencia | Cada etapa paralelizada tiene una implementación secuencial de referencia con la misma interfaz. | M | OE3 |
| RF-35 | Paralelización multihilo con OpenMP | Limpieza y cálculo de variables (rezagos, medias móviles, variaciones) sobre bloques de series en memoria compartida mediante núcleos C/C++ con OpenMP, invocables desde Python. Número de hilos configurable. | M | OE3 |
| RF-36 | Procesamiento distribuido con MPI | Reparte entre procesos MPI: (a) el procesamiento de series o fuentes, (b) los orígenes de validación móvil, (c) las semillas del ensamble y (d) las configuraciones de hiperparámetros. El proceso raíz reúne los resultados. Número de procesos configurable. | M | OE3 |
| RF-37 | Entrenamiento de la LSTM en GPU con CUDA | Entrena la LSTM en GPU por lotes y entrena muchos modelos (uno por serie o categoría) de forma simultánea. Si no hay GPU, continúa en CPU y lo registra. | M | OE3 |
| RF-38 | Estrategia de ejecución configurable | El usuario o la configuración elige: secuencial, OpenMP (*h* hilos), MPI (*p* procesos), CUDA o MPI + CUDA, sin cambiar el código del pipeline. | M | OE3, T2 |
| RF-39 | Verificación de equivalencia | Pruebas automáticas comprueban que las versiones paralelas producen los mismos resultados que la secuencial (tolerancia numérica definida; idénticos con semillas fijas en CPU). | M | OE3 |
| RF-40 | Medición de rendimiento paralelo | Mide tiempos de entrenamiento y predicción, aceleración *S(p) = T₁/Tₚ*, eficiencia *E(p) = S(p)/p* y estima la fracción paralelizable *f* (ley de Amdahl), con repeticiones, y registra el hardware usado. | M | OE3, OE4, T2 |

### 3.6 Módulo de evaluación y validación

| ID | Requerimiento | Descripción y criterio de aceptación | Prior. | Traza |
|---|---|---|---|---|
| RF-41 | Métricas de error | Calcula RMSE, MAPE y MAE por serie y agregadas en cada origen móvil; para series con ceros calcula además WAPE, sMAPE o MASE y reporta cuántos puntos se excluyeron del MAPE. | M | OE4, T2, RS |
| RF-42 | Comparación controlada de modelos | Compara modelos con los mismos datos, particiones, semillas, repeticiones y hardware; genera la tabla comparativa con media y rango por grupo de semillas. | M | OE4, T2 |
| RF-43 | Prueba de significancia | Aplica la prueba de Diebold-Mariano o de Wilcoxon a las diferencias entre modelos. | S | OE4, RS |
| RF-44 | Análisis de ablación fronteriza | Evalúa cada modelo con y sin variables fronterizas para cuantificar el aporte del comercio transfronterizo. | M | OE1, OE4 |
| RF-45 | Informe de validación | Genera un informe exportable (HTML/PDF y CSV) con métricas de error, rendimiento paralelo e indicadores de inventario. | M | OE4, PE |

### 3.7 Módulo de gestión de inventarios

| ID | Requerimiento | Descripción y criterio de aceptación | Prior. | Traza |
|---|---|---|---|---|
| RF-46 | Catálogo de productos | Registra productos por comercio: código, nombre, categoría, costo, precio, tiempo de reposición, stock actual y nivel de servicio objetivo. | M | OG |
| RF-47 | Política de reposición | Calcula stock de seguridad a partir de la incertidumbre del pronóstico (desviación del error o intervalos), punto de reorden y cantidad sugerida de pedido. | M | OG, RS |
| RF-48 | Riesgo de quiebre | Clasifica cada producto en riesgo crítico, preventivo u óptimo y calcula los días de cobertura. | M | OG |
| RF-49 | Recomendaciones de compra | Genera una lista priorizada de compras sugeridas, exportable, con la explicación de cada recomendación. | M | OG, PE |
| RF-50 | Simulación retrospectiva de inventario | Simula sobre el histórico la política de reposición guiada por el pronóstico frente a la política empírica o ingenua y calcula nivel de servicio, quiebres de stock, inventario promedio, rotación y costo. | M | OE4, T2 |
| RF-51 | Simulador de escenarios | Permite plantear escenarios hipotéticos (variación del flujo fronterizo, TRM o inflación) que se propagan por los modelos con exógenas, y guardarlos. Los resultados se marcan como hipotéticos. | S | OG |
| RF-52 | Órdenes de reabastecimiento | Registra órdenes de compra generadas desde las recomendaciones y su estado. | C | OG |

### 3.8 Módulo de visualización (dashboard)

| ID | Requerimiento | Descripción y criterio de aceptación | Prior. | Traza |
|---|---|---|---|---|
| RF-53 | Panel principal | Muestra demanda proyectada, productos en riesgo, error del modelo vigente y alertas del comercio. | M | PE |
| RF-54 | Consulta de pronósticos | Consulta por producto, categoría, punto de venta y rango de fechas: histórico, pronóstico, intervalos y eventos marcados. | M | PE |
| RF-55 | Patrones de consumo | Muestra tendencia, estacionalidad, inflación local y relación con la frontera. | M | OE1, PE |
| RF-56 | Comparación de modelos | Muestra la tabla y gráficas comparativas de métricas por modelo. | M | OE4 |
| RF-57 | Rendimiento paralelo | Muestra tiempos, aceleración y eficiencia frente al límite de Amdahl por estrategia de ejecución. | M | OE3 |
| RF-58 | Inventario y recomendaciones | Muestra el estado del inventario, el riesgo y las compras sugeridas. | M | OG, PE |
| RF-59 | Gestión de cargas de datos | Permite cargar archivos, ver su reporte de calidad y su versión. | M | OE4 |
| RF-60 | Exportación | Exporta tablas y gráficos (CSV, PNG, PDF). | S | PE |
| RF-61 | Transparencia del pronóstico | Cada pronóstico muestra el origen de los datos (real, público o sintético), el modelo y versión que lo generó, la fecha de entrenamiento y un aviso de que es un resultado automatizado de apoyo a la decisión. | M | ML (AI Act, CONPES 4144) |

### 3.9 Módulo de seguridad, administración y operación

| ID | Requerimiento | Descripción y criterio de aceptación | Prior. | Traza |
|---|---|---|---|---|
| RF-62 | Autenticación | Inicio de sesión con usuario y contraseña. | M | ML (seguridad) |
| RF-63 | Roles y aislamiento por comercio | Roles Administrador, Analista y Comerciante. Un comerciante solo ve los datos de su comercio. | M | ML (Ley 1581) |
| RF-64 | Gestión de trabajos | Lanza entrenamientos, validaciones y benchmarks como trabajos en segundo plano; muestra estado, progreso y registros; permite cancelarlos. | M | OE3 |
| RF-65 | Bitácora de auditoría | Registra cargas, entrenamientos, cambios de inventario y accesos administrativos. | S | ML (ISO 27001) |
| RF-66 | API documentada | Todas las funciones se exponen por una API REST documentada con OpenAPI. | M | PE |

**Total:** 66 requerimientos funcionales (54 M, 10 S, 2 C).

---

## 4. Requerimientos no funcionales

Se organizan según las características de calidad de la norma ISO/IEC 25010, más dos categorías propias del proyecto: cumplimiento legal y reproducibilidad científica.

### 4.1 Adecuación funcional y exactitud

| ID | Requerimiento | Métrica / criterio de verificación | Prior. | Traza |
|---|---|---|---|---|
| RNF-01 | Superar la línea base | El modelo seleccionado debe obtener menor RMSE y MAPE que el ingenuo estacional en el conjunto de prueba con origen móvil, en cada nivel de agregación evaluado. Si no lo logra, el sistema usa y reporta el mejor modelo. | M | OE4, T2 |
| RNF-02 | Metas de precisión orientativas | Serie mensual agregada: MAPE ≤ 5 % (el piloto logró 3,82 %). Producto o categoría semanal: MAPE (o WAPE) ≤ 15 %. Son metas, no condiciones de aceptación: el resultado se reporta tal como sea. | S | OE4 |

### 4.2 Eficiencia de desempeño

| ID | Requerimiento | Métrica / criterio de verificación | Prior. | Traza |
|---|---|---|---|---|
| RNF-03 | Eficiencia paralela con MPI | En la validación con origen móvil, eficiencia *E(p)* ≥ 0,70 para *p* hasta el número de núcleos físicos (el piloto obtuvo 0,94 con *p* = 2). | S | OE3 |
| RNF-04 | Aceleración con CUDA | Entrenamiento simultáneo de ≥ 200 series en GPU con aceleración ≥ 5× frente a la CPU secuencial. Es una hipótesis a evaluar; se reporta el valor obtenido. | S | OE3 |
| RNF-05 | Volumen de datos | El pipeline de preparación procesa ≥ 1 millón de registros transaccionales (≥ 500 series) sin agotar 8 GB de RAM. | M | OE2, OE3 |
| RNF-06 | Tiempo de respuesta | Consultas de pronósticos ya calculados: < 1 s (p95). Carga inicial del dashboard: < 3 s en red local. | S | PE |
| RNF-07 | Hardware accesible | La consulta y el pronóstico con modelos ya entrenados funcionan en un equipo de 8 GB de RAM sin GPU. La GPU solo es necesaria para acelerar el entrenamiento. | M | Justificación práctica |

### 4.3 Compatibilidad y portabilidad

| ID | Requerimiento | Métrica / criterio de verificación | Prior. | Traza |
|---|---|---|---|---|
| RNF-08 | Multiplataforma | Ejecuta en Windows 10/11 (desarrollo; MPI con MS-MPI o WSL2) y Linux (OpenMPI). Despliegue reproducible con Docker Compose. | M | Marco contextual |
| RNF-09 | Interoperabilidad | API REST JSON con especificación OpenAPI 3; importación CSV y XLSX; exportación CSV, PNG y PDF. | M | PE |

### 4.4 Usabilidad

| ID | Requerimiento | Métrica / criterio de verificación | Prior. | Traza |
|---|---|---|---|---|
| RNF-10 | Lenguaje y accesibilidad | Interfaz en español, con lenguaje no técnico para el comerciante (glosario y ayudas contextuales), adaptable a móvil y tableta, y contraste y navegación acordes con WCAG 2.1 AA. | M | OG, [5] |
| RNF-11 | Facilidad de uso | En una prueba con comerciantes, consultar el pronóstico de un producto y su recomendación de compra toma ≤ 3 interacciones; puntaje SUS ≥ 68. | S | OE4 |

### 4.5 Fiabilidad

| ID | Requerimiento | Métrica / criterio de verificación | Prior. | Traza |
|---|---|---|---|---|
| RNF-12 | Aislamiento de fallos | La falla de un entrenamiento no afecta la consulta de pronósticos vigentes. Los trabajos fallidos quedan registrados y se pueden reintentar. | M | OE3 |
| RNF-13 | Degradación controlada | Sin GPU o sin MPI, el sistema continúa en modo secuencial o CPU y lo informa. | M | OE3 |
| RNF-14 | Respaldo | Respaldo automatizado de la base de datos y de los artefactos de modelos, con procedimiento de restauración probado. | S | ML (ISO 27001) |

### 4.6 Seguridad

| ID | Requerimiento | Métrica / criterio de verificación | Prior. | Traza |
|---|---|---|---|---|
| RNF-15 | Credenciales | Contraseñas con hash Argon2 o bcrypt; tokens con expiración; secretos solo en variables de entorno (archivo `.env` fuera del control de versiones). | M | ML (Ley 1273) |
| RNF-16 | Validación de entradas | Validación de esquemas en la API (Pydantic) y en el frontend (zod); límites de tamaño de archivos; acceso a la base de datos solo mediante ORM o consultas parametrizadas; CORS restringido. | M | ML (Ley 1273) |
| RNF-17 | Mínimo privilegio | Control de acceso por rol y por comercio en cada endpoint, verificado con pruebas automáticas. | M | ML (ISO 27001) |
| RNF-18 | Transporte seguro | HTTPS en cualquier despliegue fuera del equipo local. | S | ML (ISO 27001) |

### 4.7 Cumplimiento legal y ético

| ID | Requerimiento | Métrica / criterio de verificación | Prior. | Traza |
|---|---|---|---|---|
| RNF-19 | Protección de datos personales | Privacidad desde el diseño: anonimización antes del procesamiento, finalidad académica declarada, autorización del comerciante registrada y ningún dato crudo de comercios en el repositorio. | M | ML (Ley 1581, RGPD) |
| RNF-20 | Transparencia algorítmica | Cada modelo publicado tiene una ficha (*model card*) con datos usados, variables y su justificación, métricas, limitaciones y uso previsto. El sistema recomienda; la decisión es del comerciante (control humano). | M | ML (Circular SIC 002/2024, CONPES 4144, AI Act) |
| RNF-21 | Sin precios dinámicos | El sistema no fija ni modifica precios al consumidor. | M | ML (Ley 1480, Ley 2439) |
| RNF-22 | Licenciamiento | Solo dependencias de código abierto con licencias compatibles; inventario de licencias de dependencias; licencia del proyecto definida en el repositorio. | M | ML (Ley 23 de 1982, Ley 603 de 2000) |

### 4.8 Mantenibilidad

| ID | Requerimiento | Métrica / criterio de verificación | Prior. | Traza |
|---|---|---|---|---|
| RNF-23 | Arquitectura modular | El núcleo analítico no depende de la API ni de la interfaz; la API es la única vía de acceso a la base de datos para el frontend. | M | — |
| RNF-24 | Calidad de código | Python: ruff (estilo y errores) y mypy sin errores. TypeScript: modo estricto y ESLint sin errores. Cobertura de pruebas ≥ 80 % en el núcleo analítico y ≥ 60 % en la API. Integración continua en cada *pull request*. | M | — |
| RNF-25 | Configuración externa | Parámetros de datos, modelos, paralelismo e inventario en archivos YAML o variables de entorno; sin valores quemados en el código. | M | T2 |
| RNF-26 | Documentación | README con instalación y uso; docstrings; decisiones de arquitectura (ADR); diagramas de arquitectura; documentación de la API; guía de usuario y guía de adopción para MIPYMES. | M | PE |

### 4.9 Reproducibilidad científica

| ID | Requerimiento | Métrica / criterio de verificación | Prior. | Traza |
|---|---|---|---|---|
| RNF-27 | Experimentos reproducibles | Semillas fijas; versión de datos (hash), de código (commit) y de entorno (archivos de bloqueo) registradas en cada experimento. Repetir un experimento en el mismo hardware da las mismas métricas. | M | T2 |
| RNF-28 | Trazabilidad de resultados | Toda tabla y figura del informe final se regenera con un comando desde los datos originales. | M | T2, OE1–OE4 |
| RNF-29 | Observabilidad | Registros estructurados por proceso (incluidos los procesos MPI) y por trabajo, con nivel y marca de tiempo. | S | OE3 |

**Total:** 29 requerimientos no funcionales (21 M, 8 S).

---

## 5. Restricciones de diseño

Estas restricciones vienen del documento del proyecto y no son negociables sin modificarlo:

1. **Metodología:** CRISP-DM adaptada con PCAM; primero la versión secuencial y luego las paralelas.
2. **Lenguajes:** Python para el modelado y análisis; C/C++ con OpenMP, MPI y CUDA para las implementaciones paralelas (MPI puede usarse desde Python con `mpi4py` y CUDA mediante PyTorch).
3. **Algoritmos:** ARIMA/SARIMA, Prophet y LSTM, comparados con un pronóstico ingenuo estacional (Tabla 2).
4. **Métricas:** RMSE y MAPE para la precisión; tiempo, aceleración y eficiencia para el rendimiento; indicadores de inventario para la gestión.
5. **Licenciamiento:** solo software de código abierto, sin costos de licencias.
6. **Validación:** particiones cronológicas con origen móvil; mismas condiciones para todos los modelos.

## 6. Decisiones de alcance

| Decisión | Justificación |
|---|---|
| Se implementan **ARIMA/SARIMA, Prophet y LSTM** aunque el informe ya seleccionó la LSTM. | La Tabla 2 define el algoritmo como variable independiente y la revisión sistemática recomienda comparar siempre la LSTM con referencias estadísticas, que pueden ganar en series cortas de PYMES. |
| Los modelos de *gradient boosting* del plan de dos semanas (LightGBM, XGBoost, Random Forest) pasan a **prioridad C**. | No están en los objetivos del documento; se conservan como línea de mejora sugerida por la revisión. |
| El sistema soporta **frecuencia diaria, semanal y mensual**. | El informe usa series mensuales y la unidad de análisis del documento es diaria o semanal por producto. |
| Los datos sintéticos se usan **solo** para desarrollo y escalabilidad. | No permiten concluir nada sobre el comercio real; la relación con la frontera está puesta por construcción. |
| Si no se obtienen datos de comercios, el OE4 se valida con las series regionales y se declara como limitación. | Es la limitación ya reconocida en el informe de OE1/OE2. |

---

## 7. Matriz de trazabilidad

### 7.1 Objetivos → requerimientos

| Objetivo | Requerimientos funcionales | Requerimientos no funcionales | Evidencia que produce el sistema |
|---|---|---|---|
| **OE1** Patrones de consumo | RF-01 a RF-05, RF-07, RF-18 a RF-23, RF-44, RF-55 | RNF-28 | Inventario de fuentes, reporte de calidad, figuras de tendencia, estacionalidad, inflación y correlación con la frontera. |
| **OE2** Selección de algoritmos y paralelización | RF-12 a RF-17, RF-24 a RF-28, RF-35 a RF-38 (diseño) | RNF-05, RNF-25, RNF-27 | Panel preparado, tabla comparativa de modelos candidatos, diseño PCAM (partición y comunicación). |
| **OE3** Sistema paralelo (MPI, CUDA) | RF-10, RF-14, RF-27, RF-29 a RF-32, RF-34 a RF-40, RF-57, RF-64 | RNF-03, RNF-04, RNF-12, RNF-13, RNF-29 | Sistema que pronostica de extremo a extremo; tablas de tiempo, aceleración y eficiencia; pruebas de equivalencia. |
| **OE4** Validación (error e inventarios) | RF-06, RF-41 a RF-45, RF-50, RF-56, RF-59 | RNF-01, RNF-02, RNF-11, RNF-27, RNF-28 | Informe de validación: RMSE/MAPE frente a líneas base, significancia, indicadores de inventario, prueba de usabilidad. |
| **OG** Optimizar inventarios y decisiones | RF-30, RF-46 a RF-54, RF-58, RF-60, RF-61 | RNF-07, RNF-10 | Dashboard con pronósticos y recomendaciones de compra. |

### 7.2 Producto esperado → requerimientos

| Producto esperado (documento) | Requerimientos |
|---|---|
| Modelos de ML optimizados (ARIMA, Prophet, LSTM) calibrados para el contexto regional | RF-24 a RF-33, RF-41 a RF-44 |
| Infraestructura de cómputo paralelo (OpenMP, MPI, CUDA) | RF-34 a RF-40, RF-64 |
| Dashboard interactivo con predicciones, tendencias y recomendaciones de inventario | RF-46 a RF-61 |
| Documentación metodológica y guía de adopción para MIPYMES | RF-45, RNF-20, RNF-26, RNF-28 |

### 7.3 Marco legal → requerimientos

| Norma | Requerimientos |
|---|---|
| Ley 1581 de 2012, RGPD (privacidad desde el diseño) | RF-08, RF-09, RF-63, RNF-19 |
| Circular SIC 002 de 2024, CONPES 4144, AI Act | RF-17, RF-61, RNF-20 |
| Ley 23 de 1982, Ley 603 de 2000, Decisión 351 CAN | RNF-22 |
| Ley 1480 de 2011, Ley 2439 de 2024 | RNF-21 |
| Ley 1273 de 2009, ISO/IEC 27001 | RF-62, RF-65, RNF-14 a RNF-18 |
