"""Las cifras del OE1 del informe se regeneran desde los archivos originales (HU-08).

Requiere los datos públicos en ``data/raw/public`` (no se versionan): se omite en la
integración continua y se ejecuta en los equipos del proyecto después de
``python -m forecast_core.pipelines.ingest descargar``.
"""

import pytest

from forecast_core.config import load_yaml, resolve_path
from forecast_core.ingestion.common import RAW_PUBLIC_DIR

CFG = load_yaml("configs/data_sources.yaml")
ARCHIVOS = [CFG["dane_emc"]["archivo"], CFG["migracion_colombia"]["archivo"], CFG["trm"]["archivo"]]
FALTAN = [a for a in ARCHIVOS if not (resolve_path(RAW_PUBLIC_DIR) / a).exists()]

pytestmark = [
    pytest.mark.datos,
    pytest.mark.skipif(bool(FALTAN), reason=f"faltan datos públicos: {FALTAN}"),
]


def test_cifras_del_informe_coinciden(tmp_path: object, monkeypatch: pytest.MonkeyPatch) -> None:
    from forecast_core.pipelines import reproduce_oe1

    checks, figs = reproduce_oe1.run()
    difieren = [c.as_row() for c in checks if c.estado == "difiere"]
    assert not difieren, difieren
    coinciden = sum(c.estado == "coincide" for c in checks)
    assert coinciden >= 23
    assert all(p.exists() for p in figs.values())
