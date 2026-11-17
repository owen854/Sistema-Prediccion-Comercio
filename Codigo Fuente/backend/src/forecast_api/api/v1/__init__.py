"""Versión 1 de la API. Cada recurso tiene su router (``03_Arquitectura_Sistema.md``, sección 8)."""

from fastapi import APIRouter

from forecast_api.api.v1 import datasets

api_router = APIRouter()
api_router.include_router(datasets.router, tags=["datos"])
