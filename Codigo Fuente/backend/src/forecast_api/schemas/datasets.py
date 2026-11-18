"""Esquemas de comercios, autorizaciones y conjuntos de datos."""

from __future__ import annotations

from datetime import date, datetime
from typing import Any

from pydantic import BaseModel, ConfigDict, Field

from forecast_api.db.models import OrigenDatos


class ComercioCreate(BaseModel):
    municipio: str = Field(min_length=2, max_length=80)
    tipo_negocio: str | None = Field(default=None, max_length=80)


class ComercioOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    codigo_seudonimo: str
    municipio: str
    tipo_negocio: str | None


class AutorizacionCreate(BaseModel):
    fecha: date
    alcance: str = Field(min_length=10, max_length=2000)
    documento_ref: str | None = Field(default=None, max_length=255)


class AutorizacionOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    comercio_id: int
    fecha: date
    alcance: str
    finalidad: str
    documento_ref: str | None


class DatasetVersionOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    version: int
    sha256: str
    archivo_original: str
    filas: int
    columnas_eliminadas: list[str]
    autorizacion_id: int | None
    creado_en: datetime


class DatasetOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    nombre: str
    origen: OrigenDatos
    fuente: str
    frecuencia: str
    comercio_id: int | None
    creado_en: datetime
    versiones: list[DatasetVersionOut]


class CargaOut(BaseModel):
    dataset_id: int
    version: DatasetVersionOut
    nueva: bool = Field(description="False si el mismo archivo ya se había cargado.")
    reporte_calidad: dict[str, Any]


class SerieOut(BaseModel):
    id: int
    clave: str
    nivel: str
    observaciones: int
    desde: date | None
    hasta: date | None


class ProblemaOut(BaseModel):
    mensaje: str
    fila: int | None = None
    columna: str | None = None


class ErrorCargaOut(BaseModel):
    detalle: str
    problemas: list[ProblemaOut] = []
