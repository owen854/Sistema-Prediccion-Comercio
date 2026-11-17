"""Endpoint de salud: estado de la API, la base de datos y los recursos de cómputo."""

from __future__ import annotations

import logging

from fastapi import APIRouter
from sqlalchemy import text
from sqlalchemy.exc import SQLAlchemyError

from forecast_api import __version__
from forecast_api.db.session import get_engine
from forecast_api.schemas.health import Capacidades, HealthResponse
from forecast_core.hpc import cuda, mpi, omp

router = APIRouter()
log = logging.getLogger(__name__)


def _database_ok() -> bool:
    try:
        with get_engine().connect() as conn:
            conn.execute(text("SELECT 1"))
    except SQLAlchemyError as exc:
        log.warning("Base de datos no disponible: %s", exc.__class__.__name__)
        return False
    return True


@router.get("/health", response_model=HealthResponse, tags=["salud"])
def health() -> HealthResponse:
    db_ok = _database_ok()
    return HealthResponse(
        status="ok" if db_ok else "degradado",
        version=__version__,
        base_de_datos="ok" if db_ok else "no_disponible",
        capacidades=Capacidades(
            openmp_kernels=omp.KERNELS_AVAILABLE,
            mpi4py=mpi.MPI_AVAILABLE,
            cuda=bool(cuda.cuda_info()["cuda_available"]),
        ),
    )
