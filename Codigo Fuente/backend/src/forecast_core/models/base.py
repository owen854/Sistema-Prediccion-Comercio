"""Interfaz común de los modelos de pronóstico (RF-28).

Todos los modelos (ingenuos, SARIMA, Prophet, LSTM) implementan ``fit`` y
``predict`` sobre matrices ``(T, N)``, para compararse bajo las mismas
condiciones (Tabla 2 del documento del proyecto).
"""

from __future__ import annotations

import pickle
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from pathlib import Path
from typing import Self

import numpy as np


@dataclass(frozen=True)
class Forecast:
    """Pronóstico de ``horizon`` periodos para N series.

    Attributes
    ----------
    mean:
        Pronóstico puntual ``(horizon, N)``.
    intervals:
        Intervalos de predicción por nivel de confianza, p. ej.
        ``{0.95: (inferior, superior)}``, cada uno ``(horizon, N)`` (RF-30).
    """

    mean: np.ndarray
    intervals: dict[float, tuple[np.ndarray, np.ndarray]] = field(default_factory=dict)

    @property
    def horizon(self) -> int:
        return int(self.mean.shape[0])


def as_2d(y: np.ndarray) -> np.ndarray:
    """Convierte una serie 1D en matriz ``(T, 1)``; valida que sea 1D o 2D."""
    arr = np.asarray(y, dtype=float)
    if arr.ndim == 1:
        return arr[:, None]
    if arr.ndim != 2:
        raise ValueError(f"Se esperaba un arreglo 1D o 2D, no ndim={arr.ndim}.")
    return arr


class Forecaster(ABC):
    """Clase base de todos los modelos."""

    name: str = "forecaster"

    @abstractmethod
    def fit(self, y: np.ndarray, X: np.ndarray | None = None) -> Self:
        """Ajusta el modelo con la historia ``y`` de forma ``(T, N)`` o ``(T,)``."""

    @abstractmethod
    def predict(self, horizon: int, X_future: np.ndarray | None = None) -> Forecast:
        """Pronostica ``horizon`` periodos después del final del entrenamiento."""

    def save(self, path: str | Path) -> None:
        """Guarda el modelo. Solo deben cargarse artefactos generados por el propio sistema."""
        with Path(path).open("wb") as fh:
            pickle.dump(self, fh)

    @classmethod
    def load(cls, path: str | Path) -> Self:
        with Path(path).open("rb") as fh:
            obj = pickle.load(fh)  # noqa: S301 (artefactos propios, ver docstring de save)
        if not isinstance(obj, cls):
            raise TypeError(f"El archivo contiene {type(obj).__name__}, no {cls.__name__}.")
        return obj
