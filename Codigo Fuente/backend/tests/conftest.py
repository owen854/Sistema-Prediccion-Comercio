"""Configuración común de pruebas."""

from __future__ import annotations

import shutil
from pathlib import Path

import numpy as np
import pytest

FIXTURES = Path(__file__).parent / "fixtures"


@pytest.fixture
def rng() -> np.random.Generator:
    return np.random.default_rng(1234)


@pytest.fixture
def fixtures_dir() -> Path:
    return FIXTURES


def mpiexec_path() -> str | None:
    return shutil.which("mpiexec")
