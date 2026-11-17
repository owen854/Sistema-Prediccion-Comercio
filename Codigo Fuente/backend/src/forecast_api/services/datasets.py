"""Casos de uso de conjuntos de datos: registro de versiones y carga de ventas (RF-06 a RF-11)."""

from __future__ import annotations

import hashlib
import secrets
from datetime import date
from pathlib import PurePath
from typing import Any

import pandas as pd
from sqlalchemy import func, insert, select
from sqlalchemy.orm import Session

from forecast_api.core.config import Settings
from forecast_api.db.models import (
    Autorizacion,
    Comercio,
    Dataset,
    DatasetVersion,
    Observacion,
    OrigenDatos,
    Serie,
)
from forecast_core.ingestion.transactional import read_sales_file, validate_sales
from forecast_core.privacy.anonymization import drop_personal_columns, pseudonymize_column
from forecast_core.validation.quality import quality_report


class DatasetError(Exception):
    """Error de negocio con código HTTP sugerido."""

    def __init__(self, mensaje: str, status_code: int = 422) -> None:
        super().__init__(mensaje)
        self.status_code = status_code


def create_comercio(session: Session, municipio: str, tipo_negocio: str | None) -> Comercio:
    comercio = Comercio(
        codigo_seudonimo=f"C{secrets.token_hex(5).upper()}",
        municipio=municipio.strip(),
        tipo_negocio=tipo_negocio.strip() if tipo_negocio else None,
    )
    session.add(comercio)
    session.flush()
    return comercio


def create_autorizacion(
    session: Session, comercio_id: int, fecha: date, alcance: str, documento_ref: str | None
) -> Autorizacion:
    if session.get(Comercio, comercio_id) is None:
        raise DatasetError("El comercio no existe.", 404)
    aut = Autorizacion(
        comercio_id=comercio_id, fecha=fecha, alcance=alcance.strip(), documento_ref=documento_ref
    )
    session.add(aut)
    session.flush()
    return aut


def register_version(
    session: Session,
    *,
    nombre: str,
    origen: OrigenDatos,
    fuente: str,
    frecuencia: str,
    long_df: pd.DataFrame,
    archivo: str,
    sha256: str,
    nivel: str,
    comercio_id: int | None = None,
    autorizacion_id: int | None = None,
    reporte_calidad: dict[str, Any] | None = None,
    columnas_eliminadas: list[str] | None = None,
) -> tuple[DatasetVersion, bool]:
    """Crea una versión nueva (o devuelve la existente si el archivo ya se cargó).

    ``long_df`` tiene las columnas ``date, series_id, units`` sin duplicados.
    Devuelve ``(version, creada)``.
    """
    cond = (
        Dataset.comercio_id.is_(None) if comercio_id is None else Dataset.comercio_id == comercio_id
    )
    dataset = session.scalar(select(Dataset).where(Dataset.nombre == nombre, cond))
    if dataset is None:
        dataset = Dataset(
            nombre=nombre,
            origen=origen,
            fuente=fuente,
            frecuencia=frecuencia,
            comercio_id=comercio_id,
        )
        session.add(dataset)
        session.flush()
    else:
        existing = session.scalar(
            select(DatasetVersion).where(
                DatasetVersion.dataset_id == dataset.id, DatasetVersion.sha256 == sha256
            )
        )
        if existing is not None:
            return existing, False

    last = session.scalar(
        select(func.max(DatasetVersion.version)).where(DatasetVersion.dataset_id == dataset.id)
    )
    version = DatasetVersion(
        dataset_id=dataset.id,
        version=(last or 0) + 1,
        sha256=sha256,
        archivo_original=PurePath(archivo).name[:255],
        filas=len(long_df),
        reporte_calidad=reporte_calidad or quality_report(long_df, freq=frecuencia),
        columnas_eliminadas=list(columnas_eliminadas or []),
        autorizacion_id=autorizacion_id,
    )
    session.add(version)
    session.flush()

    for clave, grupo in long_df.groupby("series_id", sort=True):
        serie = Serie(dataset_version_id=version.id, clave=str(clave)[:120], nivel=nivel)
        session.add(serie)
        session.flush()
        rows = [
            {"serie_id": serie.id, "fecha": pd.Timestamp(d).date(), "valor": float(v)}
            for d, v in zip(grupo["date"], grupo["units"], strict=True)
        ]
        session.execute(insert(Observacion), rows)
    return version, True


def upload_sales(
    session: Session,
    settings: Settings,
    *,
    content: bytes,
    filename: str,
    comercio_id: int,
    autorizacion_id: int,
    nombre: str,
) -> tuple[DatasetVersion, bool]:
    """Valida, anonimiza y registra un archivo de ventas de un comercio."""
    if len(content) > settings.max_upload_mb * 1024 * 1024:
        raise DatasetError(f"El archivo supera {settings.max_upload_mb} MB.", 413)
    comercio = session.get(Comercio, comercio_id)
    if comercio is None:
        raise DatasetError("El comercio no existe.", 404)
    aut = session.get(Autorizacion, autorizacion_id)
    if aut is None or aut.comercio_id != comercio_id:
        raise DatasetError(
            "No hay una autorización registrada de este comercio para usar sus datos "
            "(Ley 1581 de 2012).",
            409,
        )

    raw = read_sales_file(content, filename)
    raw, removed = drop_personal_columns(raw)
    sales = validate_sales(raw)
    sales = pseudonymize_column(sales, "store", settings.pseudonym_key_bytes(), "PV")
    report = quality_report(sales, freq="D")
    daily = sales.groupby(["date", "series_id"])["units"].sum().reset_index()
    return register_version(
        session,
        nombre=nombre.strip() or "Ventas",
        origen=OrigenDatos.TRANSACCIONAL,
        fuente=f"Carga del comercio {comercio.codigo_seudonimo}",
        frecuencia="D",
        long_df=daily,
        archivo=filename,
        sha256=hashlib.sha256(content).hexdigest(),
        nivel="producto",
        comercio_id=comercio_id,
        autorizacion_id=autorizacion_id,
        reporte_calidad=report,
        columnas_eliminadas=removed,
    )
