"""Ingesta de la TRM diaria COP/USD (RF-04).

Fuente: Superintendencia Financiera, publicada en datos.gov.co (dataset ``32sa-8pi3``,
API Socrata). Migrado de ``Prototipo/demand-forecast-hpc/scripts/00_download_real_data.py``.

Si la descarga falla (sin red o firewall), el CSV se puede exportar a mano desde
https://www.datos.gov.co/Econom-a-y-Finanzas/Tasa-de-Cambio-Representativa-del-Mercado-TRM/32sa-8pi3
y guardar en ``data/raw/public/trm.csv`` con las columnas ``date,trm_cop_usd``.
"""

from __future__ import annotations

import json
import urllib.parse
import urllib.request
from pathlib import Path
from typing import Any

import pandas as pd

SOCRATA_URL = "https://www.datos.gov.co/resource/32sa-8pi3.json"


def parse_trm_rows(rows: list[dict[str, Any]], hasta: str | None = None) -> pd.DataFrame:
    """Convierte las filas de la API en una serie diaria completa.

    Cada TRM rige desde ``vigenciadesde`` hasta la siguiente publicación, así que
    los días sin publicación (fines de semana y festivos) se rellenan hacia adelante.

    Parameters
    ----------
    rows:
        Filas JSON con al menos ``vigenciadesde`` y ``valor``.
    hasta:
        Último día de la serie (``AAAA-MM-DD``). Si es ``None`` se usa la última
        fecha publicada, para que el resultado no dependa del día de ejecución.
    """
    if not rows:
        raise ValueError("La API respondió sin filas.")
    df = pd.DataFrame(rows)
    df["date"] = pd.to_datetime(df["vigenciadesde"]).dt.tz_localize(None).dt.normalize()
    df["trm_cop_usd"] = df["valor"].astype(float)
    s = df.sort_values("date").drop_duplicates("date", keep="last").set_index("date")["trm_cop_usd"]
    end = pd.Timestamp(hasta) if hasta else s.index.max()
    s = s.reindex(pd.date_range(s.index.min(), end, freq="D")).ffill()
    return s.rename_axis("date").reset_index()


def load_trm_json(path: str | Path, hasta: str | None = None) -> pd.DataFrame:
    """Lee la respuesta JSON guardada de la API y la convierte en serie diaria."""
    rows = json.loads(Path(path).read_text(encoding="utf-8"))
    return parse_trm_rows(rows, hasta)


def fetch_trm(desde: str, hasta: str | None = None, timeout: int = 60) -> pd.DataFrame:
    """Descarga la TRM desde ``desde`` (``AAAA-MM-DD``). Requiere conexión a internet."""
    params = {
        "$where": f"vigenciadesde >= '{desde}T00:00:00.000'",
        "$order": "vigenciadesde ASC",
        "$limit": "50000",
    }
    url = SOCRATA_URL + "?" + urllib.parse.urlencode(params, quote_via=urllib.parse.quote)
    with urllib.request.urlopen(url, timeout=timeout) as resp:  # noqa: S310 (URL fija https)
        rows = json.loads(resp.read().decode("utf-8"))
    return parse_trm_rows(rows, hasta)
