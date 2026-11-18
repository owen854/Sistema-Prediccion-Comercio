"""Anonimización y seudonimización de datos de comercios (RF-08; Ley 1581 de 2012).

* Las columnas con datos personales de clientes se **eliminan** (no se guardan nunca).
* El comercio y el punto de venta se **seudonimizan** con HMAC-SHA256 y una clave
  secreta: el mismo valor siempre da el mismo seudónimo, pero sin la clave no se
  puede revertir ni adivinar con un diccionario.
"""

from __future__ import annotations

import hashlib
import hmac
from collections.abc import Iterable

import pandas as pd

from forecast_core.ingestion.common import normalize_text

PERSONAL_DATA_MARKERS = (
    "cliente",
    "comprador",
    "nombre",
    "apellido",
    "cedula",
    "documento",
    "identificacion",
    "telefono",
    "celular",
    "correo",
    "email",
    "direccion",
    "nit_cliente",
    "placa",
)


def personal_columns(columns: Iterable[str]) -> list[str]:
    """Columnas cuyo nombre indica datos personales."""
    found = []
    for col in columns:
        key = normalize_text(col).replace(" ", "_")
        if any(marker in key for marker in PERSONAL_DATA_MARKERS):
            found.append(col)
    return found


def drop_personal_columns(df: pd.DataFrame) -> tuple[pd.DataFrame, list[str]]:
    removed = personal_columns(df.columns)
    return df.drop(columns=removed), removed


def pseudonymize(value: str, key: bytes, prefix: str = "P") -> str:
    """Seudónimo estable: ``prefix`` + 12 caracteres hexadecimales de HMAC-SHA256."""
    if not key:
        raise ValueError("La clave de seudonimización no puede estar vacía.")
    digest = hmac.new(key, normalize_text(value).encode("utf-8"), hashlib.sha256).hexdigest()
    return f"{prefix}{digest[:12].upper()}"


def pseudonymize_column(df: pd.DataFrame, column: str, key: bytes, prefix: str) -> pd.DataFrame:
    if column not in df.columns:
        return df
    out = df.copy()
    out[column] = out[column].map(
        lambda v: pseudonymize(str(v), key, prefix) if pd.notna(v) and str(v).strip() else v
    )
    return out
