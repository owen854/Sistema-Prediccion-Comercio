"""Trabajo en segundo plano: la cola del worker vive en esta tabla (RF-64; ADR-002)."""

from __future__ import annotations

import enum
from datetime import datetime
from typing import Any

from sqlalchemy import DateTime, Enum, Float, ForeignKey, Index, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from forecast_api.db.base import Base, JSONType, TimestampMixin


class EstadoTrabajo(enum.StrEnum):
    PENDIENTE = "pendiente"
    EN_CURSO = "en_curso"
    OK = "ok"
    FALLIDO = "fallido"
    CANCELADO = "cancelado"


class Trabajo(TimestampMixin, Base):
    __tablename__ = "trabajo"
    __table_args__ = (Index("ix_trabajo_estado_creado_en", "estado", "creado_en"),)

    id: Mapped[int] = mapped_column(primary_key=True)
    tipo: Mapped[str] = mapped_column(String(40))
    parametros: Mapped[dict[str, Any]] = mapped_column(JSONType, default=dict)
    estado: Mapped[EstadoTrabajo] = mapped_column(
        Enum(
            EstadoTrabajo,
            native_enum=False,
            length=20,
            values_callable=lambda e: [m.value for m in e],
        ),
        default=EstadoTrabajo.PENDIENTE,
        server_default=EstadoTrabajo.PENDIENTE.value,
    )
    progreso: Mapped[float] = mapped_column(Float, default=0.0, server_default="0")
    intentos: Mapped[int] = mapped_column(Integer, default=0, server_default="0")
    mensaje: Mapped[str | None] = mapped_column(Text)
    ruta_registros: Mapped[str | None] = mapped_column(String(500))
    creado_por: Mapped[int | None] = mapped_column(ForeignKey("usuario.id", ondelete="SET NULL"))
    iniciado_en: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    terminado_en: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
