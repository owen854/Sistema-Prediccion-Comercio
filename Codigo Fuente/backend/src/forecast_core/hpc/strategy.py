"""Estrategias de ejecución intercambiables por configuración (RF-38).

Un pipeline pide una estrategia por nombre y le entrega tareas independientes
(orígenes de validación, semillas, series…), sin saber si se ejecutan en
secuencia o repartidas entre procesos MPI.

Estado en la Fase 0: ``secuencial`` y ``mpi`` implementadas. Las estrategias
``openmp`` (núcleos de variables) y ``cuda`` (entrenamiento en GPU) se integran
en la Fase 3; mientras tanto se usan directamente ``hpc.omp`` y ``hpc.cuda``.
"""

from __future__ import annotations

from collections.abc import Callable, Sequence
from typing import Any, Protocol, TypeVar

from forecast_core.hpc import mpi

T = TypeVar("T")
R = TypeVar("R")


class ExecutionStrategy(Protocol):
    name: str

    def map_tasks(self, fn: Callable[[T], R], tasks: Sequence[T]) -> list[R] | None:
        """Aplica ``fn`` a cada tarea. Devuelve ``None`` en procesos que no son raíz."""
        ...


class SequentialStrategy:
    """Versión de referencia: ejecuta las tareas una tras otra (RF-34)."""

    name = "secuencial"

    def map_tasks(self, fn: Callable[[T], R], tasks: Sequence[T]) -> list[R] | None:
        return [fn(t) for t in tasks]


class MPIStrategy:
    """Reparte las tareas entre los procesos lanzados con ``mpiexec -n p``."""

    name = "mpi"

    def __init__(self, comm: Any = None) -> None:
        if comm is None and not mpi.MPI_AVAILABLE:
            raise RuntimeError(
                "La estrategia 'mpi' requiere mpi4py (en WSL/Linux: uv sync --extra hpc)."
            )
        self.comm = comm if comm is not None else mpi.get_comm()

    @property
    def is_root(self) -> bool:
        return mpi.rank_and_size(self.comm)[0] == 0

    def map_tasks(self, fn: Callable[[T], R], tasks: Sequence[T]) -> list[R] | None:
        return mpi.mpi_map(fn, tasks, self.comm)


_STRATEGIES: dict[str, type[SequentialStrategy] | type[MPIStrategy]] = {
    SequentialStrategy.name: SequentialStrategy,
    MPIStrategy.name: MPIStrategy,
}


def get_strategy(name: str) -> ExecutionStrategy:
    """Crea la estrategia indicada en ``configs/hpc.yaml`` o en la línea de comandos."""
    try:
        return _STRATEGIES[name]()
    except KeyError:
        disponibles = ", ".join(sorted(_STRATEGIES))
        raise ValueError(f"Estrategia desconocida {name!r}. Disponibles: {disponibles}.") from None
