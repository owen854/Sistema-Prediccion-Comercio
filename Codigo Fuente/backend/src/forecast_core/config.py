"""Carga de configuración declarativa en YAML (RNF-25).

Las rutas relativas se resuelven contra la raíz del proyecto (la carpeta
``Codigo Fuente``), que se detecta buscando ``configs/`` y ``backend/``. En
entornos donde el paquete no está dentro del repositorio (por ejemplo, una
instalación no editable), se puede fijar con la variable de entorno
``FORECAST_PROJECT_ROOT``.
"""

from __future__ import annotations

import os
from pathlib import Path
from typing import Any

import yaml

PROJECT_ROOT_ENV = "FORECAST_PROJECT_ROOT"


def find_project_root(start: Path | None = None) -> Path:
    """Busca hacia arriba la carpeta que contiene ``configs/`` y ``backend/``."""
    here = (start or Path(__file__)).resolve()
    for candidate in (here, *here.parents):
        if (candidate / "configs").is_dir() and (candidate / "backend").is_dir():
            return candidate
    raise FileNotFoundError(
        "No se encontró la raíz del proyecto (carpeta con configs/ y backend/). "
        f"Defina la variable de entorno {PROJECT_ROOT_ENV}."
    )


def project_root() -> Path:
    """Raíz del proyecto, tomada de ``FORECAST_PROJECT_ROOT`` o detectada."""
    env = os.environ.get(PROJECT_ROOT_ENV)
    if env:
        return Path(env).resolve()
    return find_project_root()


def resolve_path(path: str | Path) -> Path:
    """Convierte una ruta relativa a la raíz del proyecto en absoluta."""
    p = Path(path)
    return p if p.is_absolute() else project_root() / p


def load_yaml(path: str | Path) -> dict[str, Any]:
    """Lee un archivo YAML y exige que su contenido sea un diccionario."""
    p = resolve_path(path)
    with p.open(encoding="utf-8") as fh:
        data = yaml.safe_load(fh)
    if data is None:
        return {}
    if not isinstance(data, dict):
        raise ValueError(f"{p} debe contener un diccionario YAML, no {type(data).__name__}.")
    return data
