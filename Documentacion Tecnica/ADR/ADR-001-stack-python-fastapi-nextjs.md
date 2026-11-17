# ADR-001: Backend en Python con FastAPI y frontend en Next.js

- **Estado:** Aceptada
- **Fecha:** 2026-11-17

## Contexto

El análisis de datos y los modelos (SARIMA, Prophet, LSTM) son de Python. El prototipo entregado tiene una interfaz en Next.js con buen diseño, pero su backend en TypeScript accede directamente a la base de datos y calcula "pronósticos" con multiplicadores fijos (ver `02_Evaluacion_Prototipo.md`). El documento del proyecto pide un dashboard interactivo para comerciantes, sin costos de licencia.

## Decisión

- Backend: **Python 3.12 con FastAPI**, Pydantic v2 y SQLAlchemy 2.
- Frontend: **Next.js + React + TypeScript + Tailwind CSS**, reutilizando el diseño del prototipo, **solo como capa de presentación**.
- Contrato entre ambos: especificación OpenAPI generada por FastAPI; los tipos de TypeScript se generan desde ella.

## Alternativas consideradas

| Alternativa | Motivo de descarte |
|---|---|
| Streamlit | Autenticación, roles y diseño móvil limitados; no reutiliza el prototipo. Queda como contingencia. |
| Plotly Dash | Mismo problema que Streamlit, en menor grado. |
| Power BI | Licencia Pro con costo, contrario a la justificación práctica del documento. |
| Mantener el backend del prototipo en TypeScript | Duplicaría la lógica que debe estar en Python. |

## Consecuencias

- El equipo trabaja con dos lenguajes; se mitiga con tipos generados y revisión cruzada.
- Next.js no tiene acceso a PostgreSQL; se elimina Drizzle.
- Toda cifra que muestra la interfaz viene de la API.
