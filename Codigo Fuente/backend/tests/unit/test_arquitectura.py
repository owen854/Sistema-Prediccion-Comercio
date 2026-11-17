"""Reglas de arquitectura verificadas automáticamente (ADR-008)."""

import ast
from pathlib import Path

import forecast_core

CORE_DIR = Path(forecast_core.__file__).parent


def test_el_nucleo_no_depende_de_la_api() -> None:
    infractores = []
    for path in CORE_DIR.rglob("*.py"):
        tree = ast.parse(path.read_text(encoding="utf-8"))
        for node in ast.walk(tree):
            names: list[str] = []
            if isinstance(node, ast.Import):
                names = [a.name for a in node.names]
            elif isinstance(node, ast.ImportFrom) and node.module:
                names = [node.module]
            if any(n.split(".")[0] == "forecast_api" for n in names):
                infractores.append(str(path.relative_to(CORE_DIR)))
    assert not infractores, f"forecast_core importa forecast_api en: {infractores}"
