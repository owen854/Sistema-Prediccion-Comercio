# ADR-008: Monorepo en `Codigo Fuente/` con uv y núcleo analítico independiente

- **Estado:** Aceptada
- **Fecha:** 2026-11-17

## Contexto

El sistema tiene un núcleo analítico, una API, núcleos C++ y un frontend que evolucionan juntos. El prototipo de Python no era instalable (usaba `sys.path.insert`) y sus dependencias no tenían versión fija.

## Decisión

- Todo el código vive en `Codigo Fuente/` (monorepo), con la estructura de `03_Arquitectura_Sistema.md`, sección 10.
- El código Python es un único proyecto (`backend/pyproject.toml`) gestionado con **uv** y un archivo de bloqueo (`uv.lock`), con dos paquetes: `forecast_core` (núcleo) y `forecast_api` (servicio web).
- **`forecast_core` no importa nada de `forecast_api`**; una prueba automática lo verifica.
- Las dependencias pesadas son opcionales (*extras*): `stats` (statsmodels, Prophet), `dl` (PyTorch), `hpc` (mpi4py), `experiments` (MLflow). El entorno base instala lo necesario para la API y las pruebas.
- Los núcleos C++ son un proyecto aparte (`hpc_kernels/`), porque se compilan con CMake.

## Alternativas consideradas

| Alternativa | Motivo de descarte |
|---|---|
| Un repositorio por componente | Coordinación de versiones innecesaria para un equipo de tres. |
| pip + `requirements.txt` | Sin archivo de bloqueo confiable entre Windows y Linux. |
| Poetry | uv es más rápido y también gestiona versiones de Python. |

## Consecuencias

- Instalar el entorno base es un solo comando: `uv sync`.
- La regla de independencia permite usar el núcleo desde cuadernos, Colab y `mpiexec` sin levantar la API.
