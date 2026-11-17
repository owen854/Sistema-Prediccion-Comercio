"""Reparto y reunión de tareas con MPI (RF-36; ADR-004).

Patrón PCAM usado por el sistema:

* **Partición:** la lista de tareas (orígenes de validación, semillas, series o
  configuraciones) se divide en bloques contiguos de tamaño equilibrado.
* **Comunicación:** el proceso raíz reparte los bloques (``scatter``) y reúne los
  resultados (``gather``).
* **Aglomeración:** cada proceso recibe un bloque, no tareas sueltas.
* **Mapeo:** un proceso por núcleo, lanzado con ``mpiexec -n p``.

Sin ``mpi4py`` (por ejemplo, en Windows) :func:`mpi_map` ejecuta en secuencia.
"""

from __future__ import annotations

import importlib
import logging
from collections.abc import Callable, Sequence
from typing import Any

log = logging.getLogger(__name__)


def _load_mpi() -> Any:
    """Importa ``mpi4py.MPI`` si está disponible; si no, devuelve ``None`` (RNF-13).

    Se carga con ``importlib`` para que ``MPI`` tenga el mismo tipo (``Any``) con y
    sin mpi4py instalado; así mypy da el mismo resultado en Windows y en Linux.
    mpi4py lanza ``RuntimeError`` (no ``ImportError``) cuando está instalado pero
    falta la biblioteca MPI del sistema (p. ej. Windows sin MS-MPI).
    """
    try:
        return importlib.import_module("mpi4py.MPI")
    except ImportError:
        return None
    except RuntimeError as exc:
        log.warning("mpi4py está instalado pero no encontró la biblioteca MPI: %s", exc)
        return None


MPI: Any = _load_mpi()
MPI_AVAILABLE = MPI is not None


def block_partition(n_items: int, n_parts: int) -> list[range]:
    """Divide ``range(n_items)`` en ``n_parts`` bloques contiguos (tamaños difieren en ≤ 1)."""
    if n_items < 0 or n_parts < 1:
        raise ValueError("n_items debe ser ≥ 0 y n_parts ≥ 1.")
    base, extra = divmod(n_items, n_parts)
    blocks, start = [], 0
    for i in range(n_parts):
        size = base + (1 if i < extra else 0)
        blocks.append(range(start, start + size))
        start += size
    return blocks


def get_comm() -> Any:
    """Comunicador global, o ``None`` si mpi4py no está instalado."""
    return MPI.COMM_WORLD if MPI_AVAILABLE and MPI is not None else None


def library_version() -> str | None:
    """Primera línea de la versión de la biblioteca MPI (OpenMPI, MS-MPI…), o ``None``."""
    if not MPI_AVAILABLE or MPI is None:
        return None
    return str(MPI.Get_library_version()).splitlines()[0].strip()


def rank_and_size(comm: Any = None) -> tuple[int, int]:
    comm = comm if comm is not None else get_comm()
    if comm is None:
        return 0, 1
    return int(comm.Get_rank()), int(comm.Get_size())


def mpi_map[T, R](fn: Callable[[T], R], tasks: Sequence[T], comm: Any = None) -> list[R] | None:
    """Aplica ``fn`` a cada tarea repartiendo los bloques entre los procesos MPI.

    Debe llamarse desde **todos** los procesos. El raíz (rank 0) recibe la lista
    completa de resultados en el orden original; los demás reciben ``None``.
    Sin MPI, o con un solo proceso, equivale a ``[fn(t) for t in tasks]``.
    """
    comm = comm if comm is not None else get_comm()
    rank, size = rank_and_size(comm)
    if comm is None or size == 1:
        return [fn(t) for t in tasks]

    chunks: list[list[T]] | None = None
    if rank == 0:
        chunks = [[tasks[i] for i in block] for block in block_partition(len(tasks), size)]
    my_tasks: list[T] = comm.scatter(chunks, root=0)
    my_results = [fn(t) for t in my_tasks]
    gathered: list[list[R]] | None = comm.gather(my_results, root=0)
    if rank != 0 or gathered is None:
        return None
    return [r for block in gathered for r in block]
