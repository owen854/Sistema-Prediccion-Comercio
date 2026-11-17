# ADR-002: Cola de trabajos en PostgreSQL

- **Estado:** Aceptada
- **Fecha:** 2026-11-17

## Contexto

Ingestas, entrenamientos, validaciones y benchmarks tardan minutos u horas y algunos se lanzan con `mpiexec`. No pueden ejecutarse dentro de una petición HTTP. El equipo desarrolla en Windows y WSL.

## Decisión

Una tabla `trabajo` en PostgreSQL funciona como cola. El worker toma el siguiente trabajo pendiente con `SELECT … FOR UPDATE SKIP LOCKED`, lo ejecuta (lanzando `mpiexec -n p python -m forecast_core.pipelines.…` cuando aplica), registra el progreso y los registros, e importa los resultados.

## Alternativas consideradas

| Alternativa | Motivo de descarte |
|---|---|
| RQ + Redis | RQ no funciona en Windows; agrega Redis. |
| Celery + Redis/RabbitMQ | Soporte limitado en Windows; infraestructura adicional para un volumen bajo. |
| `BackgroundTasks` de FastAPI | Muere con el proceso de la API; no sirve para trabajos largos ni para MPI. |

## Consecuencias

- Sin infraestructura extra; la cola queda respaldada junto con la base de datos.
- El rendimiento de la cola es suficiente para decenas de trabajos por hora, que es el volumen esperado.
- Si el volumen creciera, se puede cambiar a Celery sin tocar `forecast_core`, porque los pipelines no dependen de la cola.
