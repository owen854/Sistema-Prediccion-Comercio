"""MPI ≡ secuencial (RF-36, RF-39). Lanza ``mpiexec -n 2`` sobre un script pequeño."""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

import pytest

from forecast_core.hpc import mpi
from tests.conftest import mpiexec_path

pytestmark = [
    pytest.mark.mpi,
    pytest.mark.skipif(not mpi.MPI_AVAILABLE, reason="mpi4py no instalado"),
    pytest.mark.skipif(mpiexec_path() is None, reason="mpiexec no encontrado"),
]

SCRIPT = """
import json
from forecast_core.hpc.mpi import mpi_map, rank_and_size
res = mpi_map(lambda t: t * t, list(range(11)))
rank, size = rank_and_size()
if rank == 0:
    print(json.dumps({"size": size, "res": res}))
"""


@pytest.mark.parametrize("procesos", [2, 3])
def test_mpi_map_reparte_y_reune_en_orden(tmp_path: Path, procesos: int) -> None:
    script = tmp_path / "mpi_map.py"
    script.write_text(SCRIPT, encoding="utf-8")
    cmd = [str(mpiexec_path()), "-n", str(procesos), "--oversubscribe", sys.executable, str(script)]
    out = subprocess.run(cmd, capture_output=True, text=True, timeout=120, check=True)
    data = json.loads(out.stdout.strip().splitlines()[-1])
    assert data["size"] == procesos
    assert data["res"] == [t * t for t in range(11)]
