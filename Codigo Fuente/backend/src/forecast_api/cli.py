"""Comandos de administración de la API.

Uso::

    python -m forecast_api.cli importar-publicos

``importar-publicos`` registra en la base de datos las series públicas procesadas
(EMC, entradas por Norte de Santander, TRM e IPC si está disponible) como conjuntos de
datos versionados. Es idempotente: si el archivo no cambió, no crea otra versión.
"""

from __future__ import annotations

import argparse
from collections.abc import Sequence

import pandas as pd
from sqlalchemy.orm import sessionmaker

from forecast_api.db.models import OrigenDatos
from forecast_api.db.session import get_engine
from forecast_api.services.datasets import register_version
from forecast_core.config import load_yaml, resolve_path
from forecast_core.ingestion.common import RAW_PUBLIC_DIR, sha256_file
from forecast_core.pipelines.ingest import SOURCES_CONFIG, load_sources

PUBLIC = {
    "emc_ventas_reales": ("dane_emc", "DANE - Encuesta Mensual de Comercio"),
    "entradas_norte_de_santander": ("migracion_colombia", "Migración Colombia (datos.gov.co)"),
    "trm_promedio_mensual": ("trm", "Superintendencia Financiera (datos.gov.co)"),
}


def importar_publicos() -> list[str]:
    cfg = load_yaml(SOURCES_CONFIG)
    series = load_sources(cfg)
    factory = sessionmaker(bind=get_engine())
    lines = []
    with factory() as session:
        for nombre, s in series.items():
            key, fuente = PUBLIC.get(nombre, ("dane_ipc", "DANE - IPC"))
            archivo = cfg[key].get("archivo") or cfg[key].get("archivo_historico")
            path = resolve_path(RAW_PUBLIC_DIR / archivo)
            long_df = pd.DataFrame({"date": s.index, "series_id": nombre, "units": s.to_numpy()})
            version, nueva = register_version(
                session,
                nombre=nombre,
                origen=OrigenDatos.PUBLICO,
                fuente=fuente,
                frecuencia="MS",
                long_df=long_df,
                archivo=archivo,
                sha256=sha256_file(path),
                nivel="agregado",
            )
            lines.append(
                f"{nombre}: versión {version.version} ({'nueva' if nueva else 'sin cambios'})"
            )
        session.commit()
    return lines


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("comando", choices=["importar-publicos"])
    parser.parse_args(argv)
    for line in importar_publicos():
        print(line)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
