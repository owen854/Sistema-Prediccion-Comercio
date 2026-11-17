"""Comercio (MIPYME). Se identifica con un código seudónimo (RF-08, Ley 1581)."""

from __future__ import annotations

from sqlalchemy import String
from sqlalchemy.orm import Mapped, mapped_column

from forecast_api.db.base import Base, TimestampMixin


class Comercio(TimestampMixin, Base):
    __tablename__ = "comercio"

    id: Mapped[int] = mapped_column(primary_key=True)
    codigo_seudonimo: Mapped[str] = mapped_column(String(32), unique=True)
    municipio: Mapped[str] = mapped_column(String(80))
    tipo_negocio: Mapped[str | None] = mapped_column(String(80))
