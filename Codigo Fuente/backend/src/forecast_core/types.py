"""Tipos de datos compartidos por el núcleo analítico."""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import StrEnum

import numpy as np
import pandas as pd


class DataOrigin(StrEnum):
    """Origen de un conjunto de datos. Se muestra siempre al usuario (RF-10, RF-61)."""

    PUBLICO = "publico"
    TRANSACCIONAL = "transaccional"
    SINTETICO = "sintetico"


@dataclass(frozen=True)
class Panel:
    """Matriz alineada de *T* periodos × *N* series (RF-14).

    Es el formato que comparten todas las etapas: OpenMP y MPI reparten
    columnas (series) y CUDA recibe la matriz como tensor.

    Attributes
    ----------
    values:
        Matriz ``(T, N)`` de ``float64``. Puede contener ``NaN`` si el panel se
        construyó sin rellenar faltantes.
    index:
        Fechas de las filas (longitud *T*), ordenadas y sin repetir.
    series_ids:
        Identificadores de las columnas (longitud *N*).
    origin:
        Origen de los datos (público, transaccional o sintético).
    freq:
        Frecuencia de pandas (``"D"``, ``"W"``, ``"MS"``…).
    filled_cells:
        Cantidad de celdas que no existían en los datos originales y se rellenaron.
    """

    values: np.ndarray
    index: pd.DatetimeIndex
    series_ids: tuple[str, ...]
    origin: DataOrigin
    freq: str
    filled_cells: int = 0
    metadata: dict[str, str] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if self.values.ndim != 2:
            raise ValueError(f"values debe ser 2D (T, N); se recibió ndim={self.values.ndim}.")
        n_t, n_n = self.values.shape
        if len(self.index) != n_t:
            raise ValueError(f"index tiene {len(self.index)} fechas pero values tiene {n_t} filas.")
        if len(self.series_ids) != n_n:
            raise ValueError(
                f"series_ids tiene {len(self.series_ids)} elementos; values tiene {n_n} columnas."
            )
        if not self.index.is_monotonic_increasing or self.index.has_duplicates:
            raise ValueError("index debe estar ordenado y sin fechas repetidas.")

    @property
    def n_periods(self) -> int:
        return int(self.values.shape[0])

    @property
    def n_series(self) -> int:
        return int(self.values.shape[1])

    def to_frame(self) -> pd.DataFrame:
        """Devuelve el panel como DataFrame ancho (fechas × series)."""
        return pd.DataFrame(self.values, index=self.index, columns=list(self.series_ids))

    def slice_periods(self, start: int, stop: int) -> Panel:
        """Subpanel con las filas ``[start, stop)``, conservando el resto de atributos."""
        return Panel(
            values=self.values[start:stop],
            index=self.index[start:stop],
            series_ids=self.series_ids,
            origin=self.origin,
            freq=self.freq,
            filled_cells=self.filled_cells,
            metadata=dict(self.metadata),
        )
