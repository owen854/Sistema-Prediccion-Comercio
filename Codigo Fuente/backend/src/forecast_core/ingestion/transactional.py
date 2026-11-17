"""Carga de ventas de comercios desde CSV o Excel con la plantilla oficial (RF-06, RF-07).

Plantilla (``plantillas/plantilla_ventas_comercio.xlsx``):

=================  ===========  ====================================================
Columna            Obligatoria  Contenido
=================  ===========  ====================================================
fecha              Sí           Día de la venta (AAAA-MM-DD o DD/MM/AAAA)
codigo_producto    Sí           Código interno del producto (SKU)
cantidad           Sí           Unidades vendidas (número mayor o igual a 0)
categoria          No           Categoría del producto
valor              No           Valor total vendido en pesos
punto_venta        No           Sucursal o caja (se seudonimiza)
precio             No           Precio unitario
promocion          No           1 si el producto estaba en promoción, 0 si no
stock              No           Unidades en inventario al cierre del día
=================  ===========  ====================================================

Las columnas con datos personales de clientes se eliminan antes de procesar
(``privacy.anonymization``). El archivo se rechaza si falta una columna obligatoria o
si hay filas inválidas; el error explica qué corregir.
"""

from __future__ import annotations

import io
from dataclasses import dataclass, field
from pathlib import Path

import pandas as pd

from forecast_core.ingestion.common import normalize_text

REQUIRED = ("fecha", "codigo_producto", "cantidad")
OPTIONAL = ("categoria", "valor", "punto_venta", "precio", "promocion", "stock")
ALIASES = {
    "fecha_venta": "fecha",
    "dia": "fecha",
    "producto": "codigo_producto",
    "codigo": "codigo_producto",
    "sku": "codigo_producto",
    "referencia": "codigo_producto",
    "unidades": "cantidad",
    "cant": "cantidad",
    "valor_total": "valor",
    "total": "valor",
    "venta": "valor",
    "sucursal": "punto_venta",
    "tienda": "punto_venta",
    "caja": "punto_venta",
    "precio_unitario": "precio",
    "inventario": "stock",
}
MAX_EXAMPLES = 10


@dataclass(frozen=True)
class Issue:
    mensaje: str
    fila: int | None = None  # número de fila como lo ve el usuario (encabezado = 1)
    columna: str | None = None


@dataclass
class SalesValidationError(ValueError):
    problemas: list[Issue] = field(default_factory=list)

    def __str__(self) -> str:
        return "; ".join(p.mensaje for p in self.problemas[:3])


def read_sales_file(content: bytes, filename: str) -> pd.DataFrame:
    """Lee un CSV (separador ``,`` o ``;``) o un Excel (.xlsx) como texto."""
    suffix = Path(filename).suffix.lower()
    if suffix == ".xlsx":
        return pd.read_excel(io.BytesIO(content), dtype=str)
    if suffix == ".csv":
        for encoding in ("utf-8-sig", "latin-1"):
            try:
                text = content.decode(encoding)
                break
            except UnicodeDecodeError:
                continue
        sep = ";" if text.splitlines()[0].count(";") > text.splitlines()[0].count(",") else ","
        return pd.read_csv(io.StringIO(text), sep=sep, dtype=str)
    raise SalesValidationError([Issue(f"Formato no soportado ({suffix}). Use .csv o .xlsx.")])


def normalize_columns(df: pd.DataFrame) -> pd.DataFrame:
    """Encabezados en minúscula, sin tildes, con guion bajo, y alias a la plantilla."""
    renamed = {}
    for col in df.columns:
        key = normalize_text(col).replace(" ", "_")
        renamed[col] = ALIASES.get(key, key)
    return df.rename(columns=renamed)


def validate_sales(df: pd.DataFrame) -> pd.DataFrame:
    """Valida y tipa la tabla; devuelve el formato largo del sistema.

    Columnas de salida: ``date, series_id, units`` y, si existen, ``category``,
    ``value``, ``store``, ``price``, ``promo``, ``stock``.
    """
    data = normalize_columns(df).dropna(how="all")
    missing = [c for c in REQUIRED if c not in data.columns]
    if missing:
        raise SalesValidationError(
            [Issue(f"Falta la columna obligatoria '{c}'.", columna=c) for c in missing]
        )

    problems: list[Issue] = []
    fechas = _parse_dates(data["fecha"])
    for i in data.index[fechas.isna()]:
        problems.append(Issue("Fecha no válida.", fila=int(i) + 2, columna="fecha"))
    cantidades = pd.to_numeric(data["cantidad"].str.replace(",", ".", regex=False), errors="coerce")
    for i in data.index[cantidades.isna() | (cantidades < 0)]:
        problems.append(
            Issue(
                "La cantidad debe ser un número mayor o igual a 0.",
                fila=int(i) + 2,
                columna="cantidad",
            )
        )
    codigos = data["codigo_producto"].astype(str).str.strip()
    for i in data.index[data["codigo_producto"].isna() | (codigos == "")]:
        problems.append(
            Issue("Falta el código del producto.", fila=int(i) + 2, columna="codigo_producto")
        )
    if problems:
        extra = len(problems) - MAX_EXAMPLES
        shown = problems[:MAX_EXAMPLES]
        if extra > 0:
            shown.append(Issue(f"… y {extra} problemas más."))
        raise SalesValidationError(shown)

    out = pd.DataFrame({"date": fechas, "series_id": codigos.str.upper(), "units": cantidades})
    optional_map = {
        "categoria": "category",
        "valor": "value",
        "punto_venta": "store",
        "precio": "price",
        "promocion": "promo",
        "stock": "stock",
    }
    for src, dst in optional_map.items():
        if src in data.columns:
            col = data[src]
            out[dst] = (
                col.str.strip()
                if src in ("categoria", "punto_venta")
                else pd.to_numeric(col.str.replace(",", ".", regex=False), errors="coerce")
            )
    return out.reset_index(drop=True)


def _parse_dates(col: pd.Series) -> pd.Series:
    text = col.astype(str).str.strip()
    iso = pd.to_datetime(text, format="%Y-%m-%d", errors="coerce")
    latin = pd.to_datetime(text, format="%d/%m/%Y", errors="coerce")
    excel = pd.to_datetime(text, format="%Y-%m-%d %H:%M:%S", errors="coerce")
    return iso.fillna(latin).fillna(excel).dt.normalize()
