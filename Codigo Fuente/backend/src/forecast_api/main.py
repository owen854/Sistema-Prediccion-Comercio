"""Punto de entrada de la API.

Desarrollo::

    uv run uvicorn forecast_api.main:app --reload

Documentación interactiva (OpenAPI) en http://localhost:8000/docs.
"""

from __future__ import annotations

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from forecast_api import __version__
from forecast_api.api.v1 import api_router
from forecast_api.api.v1 import health as health_router
from forecast_api.core.config import get_settings
from forecast_api.core.logging import configure_logging


def create_app() -> FastAPI:
    settings = get_settings()
    configure_logging(settings.log_level)
    app = FastAPI(
        title=settings.app_name,
        version=__version__,
        description=(
            "Pronóstico de demanda y recomendaciones de inventario para MIPYMES del comercio "
            "minorista de Norte de Santander. Los resultados son automatizados y de apoyo a la "
            "decisión: la decisión final es del comerciante."
        ),
    )
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins,
        allow_credentials=True,
        allow_methods=["GET", "POST", "PATCH", "DELETE"],
        allow_headers=["Authorization", "Content-Type"],
    )
    app.include_router(health_router.router)
    app.include_router(api_router, prefix="/api/v1")
    return app


app = create_app()
