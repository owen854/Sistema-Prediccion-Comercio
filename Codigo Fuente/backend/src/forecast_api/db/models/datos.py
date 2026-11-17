"""Conjuntos de datos versionados, series y observaciones (RF-06 a RF-11, RF-59).

``dataset`` → ``dataset_version`` (inmutable, con hash y reporte de calidad) →
``serie`` → ``observacion``. Cada versión de un conjunto transaccional debe estar
amparada por una ``autorizacion`` del comerciante (RF-09, Ley 1581).
"""

from __future__ import annotations

import enum
from datetime import date
from typing import Any

from sqlalchemy import (
    Date,
    Enum,
    Float,
    ForeignKey,
    Integer,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from forecast_api.db.base import Base, JSONType, TimestampMixin


class OrigenDatos(enum.StrEnum):
    PUBLICO = "publico"
    TRANSACCIONAL = "transaccional"
    SINTETICO = "sintetico"


def _values(e: type[enum.StrEnum]) -> list[str]:
    return [m.value for m in e]


class Autorizacion(TimestampMixin, Base):
    """Autorización del comerciante para usar sus datos con finalidad académica."""

    __tablename__ = "autorizacion"

    id: Mapped[int] = mapped_column(primary_key=True)
    comercio_id: Mapped[int] = mapped_column(ForeignKey("comercio.id", ondelete="RESTRICT"))
    fecha: Mapped[date] = mapped_column(Date)
    alcance: Mapped[str] = mapped_column(Text)
    finalidad: Mapped[str] = mapped_column(String(120), server_default="académica")
    documento_ref: Mapped[str | None] = mapped_column(String(255))


class Dataset(TimestampMixin, Base):
    __tablename__ = "dataset"
    __table_args__ = (UniqueConstraint("nombre", "comercio_id", name="uq_dataset_nombre_comercio"),)

    id: Mapped[int] = mapped_column(primary_key=True)
    nombre: Mapped[str] = mapped_column(String(120))
    origen: Mapped[OrigenDatos] = mapped_column(
        Enum(OrigenDatos, native_enum=False, length=20, values_callable=_values)
    )
    fuente: Mapped[str] = mapped_column(String(200))
    frecuencia: Mapped[str] = mapped_column(String(8))
    comercio_id: Mapped[int | None] = mapped_column(ForeignKey("comercio.id", ondelete="RESTRICT"))

    versiones: Mapped[list[DatasetVersion]] = relationship(
        back_populates="dataset", order_by="DatasetVersion.version"
    )


class DatasetVersion(TimestampMixin, Base):
    """Versión inmutable de un conjunto de datos (RF-11)."""

    __tablename__ = "dataset_version"
    __table_args__ = (UniqueConstraint("dataset_id", "version", name="uq_dataset_version"),)

    id: Mapped[int] = mapped_column(primary_key=True)
    dataset_id: Mapped[int] = mapped_column(ForeignKey("dataset.id", ondelete="CASCADE"))
    version: Mapped[int] = mapped_column(Integer)
    sha256: Mapped[str] = mapped_column(String(64))
    archivo_original: Mapped[str] = mapped_column(String(255))
    filas: Mapped[int] = mapped_column(Integer)
    reporte_calidad: Mapped[dict[str, Any]] = mapped_column(JSONType)
    columnas_eliminadas: Mapped[list[str]] = mapped_column(JSONType, default=list)
    autorizacion_id: Mapped[int | None] = mapped_column(
        ForeignKey("autorizacion.id", ondelete="RESTRICT")
    )

    dataset: Mapped[Dataset] = relationship(back_populates="versiones")


class Serie(Base):
    __tablename__ = "serie"
    __table_args__ = (UniqueConstraint("dataset_version_id", "clave", name="uq_serie_clave"),)

    id: Mapped[int] = mapped_column(primary_key=True)
    dataset_version_id: Mapped[int] = mapped_column(
        ForeignKey("dataset_version.id", ondelete="CASCADE")
    )
    clave: Mapped[str] = mapped_column(String(120))
    nivel: Mapped[str] = mapped_column(String(20))  # producto | categoria | comercio | agregado
    unidad: Mapped[str | None] = mapped_column(String(40))


class Observacion(Base):
    __tablename__ = "observacion"

    serie_id: Mapped[int] = mapped_column(
        ForeignKey("serie.id", ondelete="CASCADE"), primary_key=True
    )
    fecha: Mapped[date] = mapped_column(Date, primary_key=True)
    valor: Mapped[float] = mapped_column(Float)
