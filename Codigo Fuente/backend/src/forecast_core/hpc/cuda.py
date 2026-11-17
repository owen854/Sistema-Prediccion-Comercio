"""Detección de GPU y selección de dispositivo para PyTorch (RF-37; ADR-005).

En el equipo de desarrollo no hay GPU NVIDIA: el entrenamiento CUDA se ejecuta en
Google Colab. Este módulo permite que el mismo código corra en ambos lugares y que
continúe en CPU si no hay GPU (RNF-13).
"""

from __future__ import annotations

import logging
from typing import Any

log = logging.getLogger(__name__)


def cuda_info() -> dict[str, Any]:
    """Describe PyTorch y la GPU disponible (se guarda con cada ejecución)."""
    try:
        import torch
    except ImportError:
        return {"torch": None, "cuda_available": False}
    available = bool(torch.cuda.is_available())
    info: dict[str, Any] = {
        "torch": str(torch.__version__),
        "cuda_available": available,
        "cuda_version": torch.version.cuda,
    }
    if available:
        props = torch.cuda.get_device_properties(0)
        info.update(
            device_name=torch.cuda.get_device_name(0),
            device_count=torch.cuda.device_count(),
            memory_gb=round(props.total_memory / 1024**3, 1),
            cudnn=torch.backends.cudnn.version(),
        )
    return info


def select_device(prefer: str = "cuda") -> str:
    """Devuelve ``"cuda"`` si se pidió y hay GPU; en otro caso ``"cpu"`` (y lo registra)."""
    if prefer == "cuda":
        if cuda_info()["cuda_available"]:
            return "cuda"
        log.warning("No hay GPU con CUDA disponible: el entrenamiento continúa en CPU.")
    return "cpu"
