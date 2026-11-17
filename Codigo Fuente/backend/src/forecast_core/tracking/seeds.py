"""Semillas fijas para experimentos reproducibles (Tabla 2 del documento; RNF-27)."""

from __future__ import annotations

import os
import random

import numpy as np


def set_global_seed(seed: int, *, deterministic_torch: bool = True) -> np.random.Generator:
    """Fija la semilla de ``random``, NumPy y PyTorch (si está instalado).

    Devuelve un ``numpy.random.Generator`` con esa semilla, que es la forma
    recomendada de generar números aleatorios dentro del sistema.
    """
    random.seed(seed)
    np.random.seed(seed)  # noqa: NPY002 (bibliotecas de terceros aún usan el estado global)
    os.environ["PYTHONHASHSEED"] = str(seed)
    try:
        import torch
    except ImportError:
        pass
    else:
        torch.manual_seed(seed)
        if torch.cuda.is_available():
            torch.cuda.manual_seed_all(seed)
        if deterministic_torch:
            torch.backends.cudnn.deterministic = True
            torch.backends.cudnn.benchmark = False
    return np.random.default_rng(seed)
