"""Pipeline de ingesta de fuentes públicas (RF-01 a RF-05, RF-07, RF-11).

Uso::

    python -m forecast_core.pipelines.ingest descargar      # baja las fuentes y las registra
    python -m forecast_core.pipelines.ingest procesar       # construye el panel mensual
    python -m forecast_core.pipelines.ingest ipc-sintetico  # IPC sintético (solo pruebas)

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
from pathlib import Path
from typing import Any

import pandas as pd

from forecast_core.config import load_yaml, resolve_path
from forecast_core.ingestion import common, dane_emc, dane_ipc, migracion, synthetic, trm
from forecast_core.types import DataOrigin
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


SYNTHETIC_DIR = Path("data") / "synthetic"


def write_synthetic_cpi(cfg: dict[str, Any]) -> Path:
    """Genera la historia SINTÉTICA del IPC por ciudades en ``data/synthetic``."""
    ipc = cfg["dane_ipc"]
    path = resolve_path(SYNTHETIC_DIR / ipc["archivo_sintetico"])
    path.parent.mkdir(parents=True, exist_ok=True)
    periodo = ipc["periodo_informe"]
    synthetic.generate_city_cpi(start=periodo["inicio"], end=periodo["fin"]).to_csv(
        path, index=False, encoding="utf-8"
    )
    common.register_in_manifest(
        path,
        fuente="Generador sintético (forecast_core.ingestion.synthetic.generate_city_cpi)",
        descripcion="IPC SINTÉTICO por ciudades: solo para probar el pipeline, no es evidencia.",
    )
    return path


def load_sources(cfg: dict[str, Any], *, permitir_sintetico: bool = False) -> dict[str, pd.Series]:
    """Lee las fuentes disponibles en disco y devuelve series mensuales (inicio de mes).

    El IPC por ciudades se toma del archivo histórico real si existe. Si no, y solo si
    ``permitir_sintetico`` es verdadero, se usa el sintético; esas series llevan
    ``attrs["origin"] = "sintetico"`` y nunca entran al panel de modelado.
    """
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

    ipc = cfg["dane_ipc"]
    real_csv = raw / ipc["archivo_historico"]
    synthetic_csv = resolve_path(SYNTHETIC_DIR / ipc["archivo_sintetico"])
    if real_csv.exists():
        ipc_csv, origin = real_csv, DataOrigin.PUBLICO
    elif permitir_sintetico and synthetic_csv.exists():
        ipc_csv, origin = synthetic_csv, DataOrigin.SINTETICO
    else:
        return series
    wide = dane_ipc.load_city_history_csv(ipc_csv)
    base = ipc["reconstruccion_indice"]["base"]
    for ciudad, nombre in (("Cúcuta", "ipc_cucuta"), ("Nacional", "ipc_nacional")):
        if ciudad in wide.columns:
            s = dane_ipc.index_from_monthly_variation(
                wide[ciudad].dropna().rename(nombre), base_date=base
            )
            s.attrs["origin"] = origin.value
            series[nombre] = s
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
    parser.add_argument("accion", choices=["descargar", "procesar", "ipc-sintetico"])
    args = parser.parse_args(argv)
    cfg = load_yaml(SOURCES_CONFIG)
    if args.accion == "ipc-sintetico":
        print(f"IPC SINTÉTICO generado en {write_synthetic_cpi(cfg)} (no es evidencia).")
        return 0
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
