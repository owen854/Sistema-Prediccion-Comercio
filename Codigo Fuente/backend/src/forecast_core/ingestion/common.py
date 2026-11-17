"""Utilidades comunes de ingesta: meses en español, manifiesto con hash y descargas (RF-11)."""

from __future__ import annotations

import hashlib
import json
import unicodedata
import urllib.parse
import urllib.request
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from forecast_core.config import project_root, resolve_path

MANIFEST_PATH = Path("data") / "manifest.json"
RAW_PUBLIC_DIR = Path("data") / "raw" / "public"

SPANISH_MONTHS = {
    "enero": 1,
    "febrero": 2,
    "marzo": 3,
    "abril": 4,
    "mayo": 5,
    "junio": 6,
    "julio": 7,
    "agosto": 8,
    "septiembre": 9,
    "setiembre": 9,
    "octubre": 10,
    "noviembre": 11,
    "diciembre": 12,
}


def normalize_text(value: object) -> str:
    """Minúsculas, sin tildes ni espacios sobrantes (para comparar encabezados y nombres)."""
    text = unicodedata.normalize("NFKD", str(value)).encode("ascii", "ignore").decode("ascii")
    return " ".join(text.lower().split())


def parse_spanish_month(value: object) -> int | None:
    """Número del mes a partir de su nombre en español (``"  Enero"`` → 1), o ``None``."""
    if value is None:
        return None
    return SPANISH_MONTHS.get(normalize_text(value).rstrip("p*"))


def sha256_file(path: str | Path) -> str:
    digest = hashlib.sha256()
    with Path(path).open("rb") as fh:
        for chunk in iter(lambda: fh.read(1 << 20), b""):
            digest.update(chunk)
    return digest.hexdigest()


def download(url: str, dest: str | Path, *, params: dict[str, str] | None = None) -> Path:
    """Descarga ``url`` (con parámetros de consulta opcionales) en ``dest``."""
    full_url = url + ("?" + urllib.parse.urlencode(params) if params else "")
    if not full_url.startswith("https://"):
        raise ValueError(f"Solo se permiten descargas por HTTPS: {full_url}")
    target = resolve_path(dest)
    target.parent.mkdir(parents=True, exist_ok=True)
    with urllib.request.urlopen(full_url, timeout=120) as resp:  # noqa: S310 (solo https, verificado)
        target.write_bytes(resp.read())
    return target


def register_in_manifest(
    path: str | Path, *, fuente: str, url: str | None = None, descripcion: str = ""
) -> dict[str, Any]:
    """Agrega o reemplaza la entrada de ``path`` en ``data/manifest.json`` con su hash SHA-256."""
    file_path = resolve_path(path)
    root = project_root()
    entry = {
        "archivo": file_path.relative_to(root).as_posix(),
        "fuente": fuente,
        "url": url,
        "descripcion": descripcion,
        "bytes": file_path.stat().st_size,
        "sha256": sha256_file(file_path),
        "registrado_en": datetime.now(UTC).isoformat(timespec="seconds"),
    }
    manifest_file = root / MANIFEST_PATH
    manifest: dict[str, Any] = (
        json.loads(manifest_file.read_text(encoding="utf-8"))
        if manifest_file.exists()
        else {"descripcion": "Registro de archivos de datos (RF-11).", "archivos": []}
    )
    files = [f for f in manifest.get("archivos", []) if f.get("archivo") != entry["archivo"]]
    files.append(entry)
    manifest["archivos"] = sorted(files, key=lambda f: str(f["archivo"]))
    manifest_file.parent.mkdir(parents=True, exist_ok=True)
    manifest_file.write_text(json.dumps(manifest, indent=2, ensure_ascii=False) + "\n", "utf-8")
    return entry
