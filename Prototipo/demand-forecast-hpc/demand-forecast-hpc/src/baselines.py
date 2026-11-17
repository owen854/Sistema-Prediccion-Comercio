"""Línea base: pronóstico ingenuo estacional (seasonal naive).

Predice que cada día se parecerá al mismo día de la semana anterior.
Es la "vara mínima": cualquier modelo complejo (SARIMA, Prophet, LSTM) debe
superarla; si no, no se justifica su costo. Está en la Tabla 2 del documento.
"""
import numpy as np


def seasonal_naive(train: np.ndarray, horizon: int, season: int = 7) -> np.ndarray:
    """train: (T, N) matriz de ventas (T días x N series). Devuelve (horizon, N)."""
    last_season = train[-season:]
    reps = int(np.ceil(horizon / season))
    return np.tile(last_season, (reps, 1))[:horizon]
