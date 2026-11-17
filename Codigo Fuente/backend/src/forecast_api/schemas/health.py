"""Esquemas del endpoint de salud."""

from __future__ import annotations

from typing import Literal

from pydantic import BaseModel


class Capacidades(BaseModel):
    """Recursos de cómputo paralelo detectados en el servidor."""

    openmp_kernels: bool
    mpi4py: bool
    cuda: bool


class HealthResponse(BaseModel):
    status: Literal["ok", "degradado"]
    version: str
    base_de_datos: Literal["ok", "no_disponible"]
    capacidades: Capacidades
