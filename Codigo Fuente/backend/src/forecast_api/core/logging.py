"""Configuración de registros (RNF-29). En la Fase 4 se pasa a formato JSON estructurado."""

from __future__ import annotations

import logging

FORMAT = "%(asctime)s %(levelname)s %(name)s [pid=%(process)d] %(message)s"


def configure_logging(level: str = "INFO") -> None:
    logging.basicConfig(level=level.upper(), format=FORMAT)
