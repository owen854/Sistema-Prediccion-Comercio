"""Usuario con rol (RF-62, RF-63). Un comerciante siempre pertenece a un comercio."""

from __future__ import annotations

import enum

from sqlalchemy import Boolean, CheckConstraint, Enum, ForeignKey, String, true
from sqlalchemy.orm import Mapped, mapped_column

from forecast_api.db.base import Base, TimestampMixin


class Rol(enum.StrEnum):
    ADMIN = "admin"
    ANALISTA = "analista"
    COMERCIANTE = "comerciante"


class Usuario(TimestampMixin, Base):
    __tablename__ = "usuario"
    __table_args__ = (
        CheckConstraint(
            "rol <> 'comerciante' OR comercio_id IS NOT NULL", name="comerciante_con_comercio"
        ),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    correo: Mapped[str] = mapped_column(String(254), unique=True)
    hash_contrasena: Mapped[str] = mapped_column(String(255))
    rol: Mapped[Rol] = mapped_column(
        Enum(Rol, native_enum=False, length=20, values_callable=lambda e: [m.value for m in e])
    )
    comercio_id: Mapped[int | None] = mapped_column(ForeignKey("comercio.id", ondelete="RESTRICT"))
    activo: Mapped[bool] = mapped_column(Boolean, server_default=true())
