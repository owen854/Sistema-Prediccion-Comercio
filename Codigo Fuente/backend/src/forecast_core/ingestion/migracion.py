"""Ingesta de entradas de extranjeros por los puestos migratorios de Norte de Santander (RF-03).

Fuente: Migración Colombia, "Entradas de extranjeros a Colombia" en datos.gov.co
(``96sh-4v8d``). Los puestos se identifican por coordenadas en la columna
"Ubicación PCM"; los de Norte de Santander están en ``configs/data_sources.yaml``.
La consulta se agrega en el servidor (año, mes, puesto), así que se descargan unos
cientos de filas en lugar de millones.
"""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd

from forecast_core.ingestion.common import download, parse_spanish_month

API_URL = "https://www.datos.gov.co/resource/96sh-4v8d.json"


def soql_params(puestos: Sequence[str]) -> dict[str, str]:
    """Parámetros SoQL: total de entradas por año, mes y puesto, solo para ``puestos``."""
    lista = ",".join("'" + p.replace("'", "''") + "'" for p in puestos)
    return {
        "$select": "a_o,mes,ubicacion_pcm,sum(total) as total",
        "$where": f"ubicacion_pcm in({lista})",
        "$group": "a_o,mes,ubicacion_pcm",
        "$limit": "50000",
    }


def download_migracion(puestos: Sequence[str], dest: str | Path) -> Path:
    return download(API_URL, dest, params=soql_params(puestos))


def parse_migracion(rows: list[dict[str, Any]], puestos: Mapping[str, str]) -> pd.DataFrame:
    """Tabla larga ``date, puesto, nombre, entradas`` (solo los puestos indicados)."""
    records = []
    for r in rows:
        puesto = str(r.get("ubicacion_pcm", ""))
        if puesto not in puestos:
            continue
        month = parse_spanish_month(r.get("mes"))
        if month is None:
            raise ValueError(f"Mes no reconocido: {r.get('mes')!r}.")
        records.append(
            {
                "date": pd.Timestamp(year=int(r["a_o"]), month=month, day=1),
                "puesto": puesto,
                "nombre": puestos[puesto],
                "entradas": float(r["total"]),
            }
        )
    if not records:
        raise ValueError("Ninguna fila corresponde a los puestos configurados.")
    return pd.DataFrame.from_records(records).sort_values(["date", "puesto"], ignore_index=True)


def monthly_entries(
    df: pd.DataFrame, faltantes: Mapping[str, float] | None = None
) -> tuple[pd.Series, list[str]]:
    """Total mensual de entradas en los puestos y lista de meses rellenados.

    Los meses sin registro se rellenan solo si están en ``faltantes`` (regla del
    informe: abril de 2020 = 0 por cierre de frontera). Si queda algún mes sin
    dato, se lanza un error para no ocultarlo.
    """
    total = df.groupby("date")["entradas"].sum()
    idx = pd.date_range(total.index.min(), total.index.max(), freq="MS")
    total = total.reindex(idx)
    values = total.to_numpy(dtype=float, copy=True)
    rellenados = []
    for mes, valor in (faltantes or {}).items():
        pos = int(idx.get_indexer(pd.DatetimeIndex([f"{mes}-01"]))[0])
        if pos >= 0 and np.isnan(values[pos]):
            values[pos] = valor
            rellenados.append(mes)
    if np.isnan(values).any():
        huecos = [d.strftime("%Y-%m") for d in idx[np.isnan(values)]]
        raise ValueError(f"Meses sin dato y sin regla de relleno: {huecos}.")
    series = pd.Series(
        values, index=pd.DatetimeIndex(idx, freq="MS"), name="entradas_norte_de_santander"
    )
    return series, rellenados
