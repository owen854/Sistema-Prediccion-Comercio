# ADR-006: MLflow local para el seguimiento de experimentos

- **Estado:** Aceptada
- **Fecha:** 2026-11-17

## Contexto

La Tabla 2 del documento exige las mismas condiciones para todos los modelos, semillas fijas y repeticiones. Cada cifra del informe debe poder rastrearse hasta la ejecución que la produjo (RNF-27, RNF-28).

## Decisión

Se usa **MLflow** con almacenamiento local (`Codigo Fuente/experiments/mlruns/`). Cada ejecución registra: configuración YAML, versión de datos (hash), commit de Git, semilla, estrategia de ejecución, hardware, métricas y artefactos. Las ejecuciones de Colab se exportan y se importan al almacén local.

## Alternativas consideradas

| Alternativa | Motivo de descarte |
|---|---|
| Tabla propia en PostgreSQL | Habría que construir la comparación y los artefactos desde cero. |
| Weights & Biases | Servicio externo; los datos saldrían del equipo. |
| Archivos CSV sueltos | Sin trazabilidad ni comparación. |

## Consecuencias

- MLflow se instala como dependencia opcional (`experiments`) para no cargar el entorno base.
- La tabla `modelo_publicado` de la base de datos guarda el identificador de la ejecución de MLflow.
