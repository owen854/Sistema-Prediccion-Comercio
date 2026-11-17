"""Modelos de la base de datos (``03_Arquitectura_Sistema.md``, sección 7).

Cada entidad se agrega en la fase que la necesita, con su migración.
"""

from forecast_api.db.models.comercio import Comercio
from forecast_api.db.models.datos import (
    Autorizacion,
    Dataset,
    DatasetVersion,
    Observacion,
    OrigenDatos,
    Serie,
)
from forecast_api.db.models.trabajo import EstadoTrabajo, Trabajo
from forecast_api.db.models.usuario import Rol, Usuario

__all__ = [
    "Autorizacion",
    "Comercio",
    "Dataset",
    "DatasetVersion",
    "EstadoTrabajo",
    "Observacion",
    "OrigenDatos",
    "Rol",
    "Serie",
    "Trabajo",
    "Usuario",
]
