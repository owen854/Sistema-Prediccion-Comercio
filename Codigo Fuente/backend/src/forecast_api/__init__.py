"""API REST del Sistema de Predicción de Demanda (FastAPI).

Es la única puerta de acceso a la base de datos para el frontend (ADR-001).
"""

from forecast_core import __version__

__all__ = ["__version__"]
