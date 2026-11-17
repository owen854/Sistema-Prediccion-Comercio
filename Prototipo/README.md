# Prototipo (referencia histórica, solo lectura)

Esta carpeta conserva el prototipo entregado por el equipo antes de la Fase 0. **Ya no se desarrolla aquí**: el sistema vive en `Codigo Fuente/`.

| Subcarpeta | Qué se hizo con ella |
|---|---|
| `demand-forecast-hpc/` | Sus módulos (métricas, origen móvil, línea base, panel, calidad, generador sintético, TRM) se migraron a `Codigo Fuente/backend/src/forecast_core/`. Una prueba verifica que reproducen exactamente sus resultados. |
| `retail-demand-prediction-system/` | Se reutilizaron el diseño visual y la estructura de la interfaz en `Codigo Fuente/frontend/`. **Su motor de predicción, sus datos semilla y la tabla de comparación de modelos se descartaron porque no los calcula ningún modelo**; esas cifras no deben usarse en la monografía ni en presentaciones. |

Detalle en `Documentacion Tecnica/02_Evaluacion_Prototipo.md`.
