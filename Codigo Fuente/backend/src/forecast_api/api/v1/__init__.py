"""Versión 1 de la API. Cada recurso tiene su router (``03_Arquitectura_Sistema.md``, sección 8)."""

from fastapi import APIRouter

api_router = APIRouter()

# Los routers de recursos se agregan aquí a partir de la Fase 1:
# api_router.include_router(datasets.router, prefix="/datasets", tags=["datasets"])
