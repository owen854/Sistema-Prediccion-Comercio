"""Validación con origen móvil (RF-16), migrada de ``validation.py`` del prototipo.

En series de tiempo no se puede mezclar el orden (como en un ``train_test_split``
aleatorio) porque el modelo vería el futuro durante el entrenamiento (fuga de
información). Cada partición (*fold*) entrena con todo lo anterior a un origen
``t0`` y prueba en los ``horizon`` periodos siguientes::

    |-------- entrenamiento --------|-- prueba --|
    0                               t0          t0+h

En la siguiente partición el origen avanza ``step`` periodos y se repite.
"""

from __future__ import annotations

from collections.abc import Iterator, Sequence
from dataclasses import dataclass


@dataclass(frozen=True)
class Fold:
    """Partición de origen móvil. Los límites son exclusivos."""

    index: int
    train_end: int  # entrena con [0, train_end)
    test_end: int  # prueba en [train_end, test_end)

    @property
    def horizon(self) -> int:
        return self.test_end - self.train_end


def rolling_origin_folds(
    n_obs: int, horizon: int, n_folds: int, step: int | None = None
) -> Iterator[Fold]:
    """Genera ``n_folds`` particiones; la última termina exactamente en ``n_obs``."""
    if horizon < 1 or n_folds < 1:
        raise ValueError("horizon y n_folds deben ser mayores o iguales a 1.")
    step = step or horizon
    last_train_end = n_obs - horizon
    first_train_end = last_train_end - step * (n_folds - 1)
    if first_train_end <= 0:
        raise ValueError("Serie demasiado corta para esa cantidad de particiones.")
    for i in range(n_folds):
        te = first_train_end + i * step
        yield Fold(index=i, train_end=te, test_end=te + horizon)


def check_no_leakage(folds: Sequence[Fold], n_obs: int) -> None:
    """Verifica que ninguna partición use datos de prueba para entrenar.

    Lanza ``ValueError`` si una partición tiene prueba vacía, se sale de la serie
    o si los orígenes no avanzan en el tiempo.
    """
    previous_end = 0
    for f in folds:
        if not 0 < f.train_end < f.test_end <= n_obs:
            raise ValueError(f"Partición {f.index} inválida: {f}.")
        if f.train_end < previous_end:
            raise ValueError(f"La partición {f.index} retrocede en el tiempo.")
        previous_end = f.train_end
