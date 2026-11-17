"""Pipeline de ingesta de fuentes públicas (RF-01 a RF-05, RF-07, RF-11).

Uso::

    python -m forecast_core.pipelines.ingest descargar      # baja las fuentes y las registra
    python -m forecast_core.pipelines.ingest procesar       # construye el panel mensual

``procesar`` lee los archivos de ``data/raw/public`` (según ``configs/data_sources.yaml``),
guarda cada serie limpia en ``data/interim/``, el panel mensual común en
``data/processed/panel_mensual.parquet`` y el reporte de calidad en
``data/processed/calidad_fuentes.json``.
"""

from __future__ import annotations

import argparse
import json
import sys
from collections.abc import Sequence
from typing import Any

import pandas as pd

from forecast_core.config import load_yaml, resolve_path
from forecast_core.ingestion import common, dane_emc, dane_ipc, migracion, trm
from forecast_core.validation.quality import quality_report

SOURCES_CONFIG = "configs/data_sources.yaml"
RAW = common.RAW_PUBLIC_DIR


def download_sources(cfg: dict[str, Any]) -> list[dict[str, Any]]:
    """Descarga EMC, Migración y TRM y las registra en el manifiesto con su hash."""
    entries = []
    emc = cfg["dane_emc"]
    url = emc["url"].format(**emc["corte_informe"])
    common.download(url, RAW / emc["archivo"])
    entries.append(
        common.register_in_manifest(
            RAW / emc["archivo"], fuente="DANE - EMC", url=url, descripcion=emc["descripcion"]
        )
    )

    mig = cfg["migracion_colombia"]
    migracion.download_migracion(list(mig["puestos_norte_de_santander"]), RAW / mig["archivo"])
    entries.append(
        common.register_in_manifest(
            RAW / mig["archivo"],
            fuente="Migración Colombia (datos.gov.co)",
            url=mig["api"],
            descripcion="Consulta agregada por año, mes y puesto de Norte de Santander",
        )
    )

    t = cfg["trm"]
    common.download(
        t["api"],
        RAW / t["archivo"],
        params={
            "$where": f"vigenciadesde >= '{t['desde']}T00:00:00.000'",
            "$order": "vigenciadesde ASC",
            "$limit": "50000",
        },
    )
    entries.append(
        common.register_in_manifest(
            RAW / t["archivo"],
            fuente="Superintendencia Financiera (datos.gov.co)",
            url=t["api"],
            descripcion=t["descripcion"],
        )
    )
    return entries


def load_sources(cfg: dict[str, Any]) -> dict[str, pd.Series]:
    """Lee las fuentes disponibles en disco y devuelve series mensuales (inicio de mes)."""
    raw = resolve_path(RAW)
    series: dict[str, pd.Series] = {}
    series["emc_ventas_reales"] = dane_emc.parse_emc_index(
        raw / cfg["dane_emc"]["archivo"],
        sheet=cfg["dane_emc"]["hoja"],
        column=cfg["dane_emc"]["columna"],
    )
    mig = cfg["migracion_colombia"]
    rows = json.loads((raw / mig["archivo"]).read_text(encoding="utf-8"))
    entries, _ = migracion.monthly_entries(
        migracion.parse_migracion(rows, mig["puestos_norte_de_santander"]), mig.get("faltantes")
    )
    series["entradas_norte_de_santander"] = entries

    trm_daily = trm.load_trm_json(raw / cfg["trm"]["archivo"]).set_index("date")["trm_cop_usd"]
    trm_monthly = trm_daily.resample("MS").mean().rename("trm_promedio_mensual")
    series["trm_promedio_mensual"] = trm_monthly

    ipc_csv = raw / cfg["dane_ipc"]["archivo_historico"]
    if ipc_csv.exists():
        wide = dane_ipc.load_city_history_csv(ipc_csv)
        base = cfg["dane_ipc"]["reconstruccion_indice"]["base"]
        for ciudad, nombre in (("Cúcuta", "ipc_cucuta"), ("Nacional", "ipc_nacional")):
            if ciudad in wide.columns:
                series[nombre] = dane_ipc.index_from_monthly_variation(
                    wide[ciudad].dropna().rename(nombre), base_date=base
                )
    return series


def quality_by_series(series: dict[str, pd.Series]) -> dict[str, Any]:
    report = {}
    for name, s in series.items():
        long = pd.DataFrame({"date": s.index, "series_id": name, "units": s.to_numpy()})
        report[name] = quality_report(long, freq="MS")
    return report


def build_panel(series: dict[str, pd.Series]) -> pd.DataFrame:
    """Panel mensual en el periodo común de todas las series (sin huecos)."""
    panel = pd.concat(series.values(), axis=1, join="inner").sort_index()
    panel.index.name = "date"
    return panel


def process(cfg: dict[str, Any]) -> dict[str, Any]:
    series = load_sources(cfg)
    interim = resolve_path("data/interim")
    interim.mkdir(parents=True, exist_ok=True)
    for name, s in series.items():
        s.to_frame().to_parquet(interim / f"{name}.parquet")
    panel = build_panel(series)
    processed = resolve_path("data/processed")
    processed.mkdir(parents=True, exist_ok=True)
    panel.to_parquet(processed / "panel_mensual.parquet")
    report = {
        "series": quality_by_series(series),
        "panel": {
            "columnas": list(panel.columns),
            "inicio": str(panel.index.min().date()),
            "fin": str(panel.index.max().date()),
            "meses": len(panel),
            "faltantes": int(panel.isna().sum().sum()),
        },
        "pendiente": []
        if "ipc_cucuta" in series
        else ["IPC por ciudades: falta el archivo histórico"],
    }
    (processed / "calidad_fuentes.json").write_text(
        json.dumps(report, indent=2, ensure_ascii=False), encoding="utf-8"
    )
    return report


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Ingesta de fuentes públicas")
    parser.add_argument("accion", choices=["descargar", "procesar"])
    args = parser.parse_args(argv)
    cfg = load_yaml(SOURCES_CONFIG)
    if args.accion == "descargar":
        for e in download_sources(cfg):
            print(f"{e['archivo']}  {e['bytes']:>9} bytes  sha256={e['sha256'][:12]}…")
        return 0
    report = process(cfg)
    json.dump(report["panel"], sys.stdout, indent=2, ensure_ascii=False)
    print()
    for p in report["pendiente"]:
        print(f"Pendiente: {p}", file=sys.stderr)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
