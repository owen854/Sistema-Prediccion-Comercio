"""Validación con origen móvil (rolling origin), como exige la metodología.

En series de tiempo NO se puede mezclar el orden (como en un train_test_split
aleatorio) porque el modelo vería el futuro durante el entrenamiento
(fuga de información / data leakage). Cada fold entrena con todo lo anterior
a un origen t0 y prueba en los horizon días siguientes.

    |-------- entrenamiento --------|-- prueba --|
    0                               t0          t0+h
Siguiente fold: el origen avanza step días y se repite.
"""
from dataclasses import dataclass
from typing import Iterator


@dataclass(frozen=True)
class Fold:
    index: int
    train_end: int   # exclusivo: entrena con [0, train_end)
    test_end: int    # exclusivo: prueba en [train_end, test_end)


def rolling_origin_folds(n_obs: int, horizon: int, n_folds: int,
                         step: int | None = None) -> Iterator[Fold]:
    """Genera n_folds folds; el último termina exactamente en n_obs."""
    step = step or horizon
    last_train_end = n_obs - horizon
    first_train_end = last_train_end - step * (n_folds - 1)
    if first_train_end <= 0:
        raise ValueError("Serie demasiado corta para esa cantidad de folds.")
    for i in range(n_folds):
        te = first_train_end + i * step
        yield Fold(index=i, train_end=te, test_end=te + horizon)
