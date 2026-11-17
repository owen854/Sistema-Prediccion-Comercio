"""Métricas de error definidas en la documentación (Hyndman & Koehler, 2006).

RMSE = sqrt( (1/n) * sum (y - yhat)^2 )
MAPE = (100/n) * sum | (y - yhat) / y |

Aviso metodológico: el MAPE no está definido cuando y = 0 (ventas diarias en
cero son comunes en comercio minorista). Aquí se excluyen esos puntos y se
reporta cuántos fueron excluidos, para no esconder el problema.
"""
import numpy as np


def rmse(y_true, y_pred) -> float:
    y_true, y_pred = np.asarray(y_true, float), np.asarray(y_pred, float)
    return float(np.sqrt(np.mean((y_true - y_pred) ** 2)))


def mape(y_true, y_pred) -> float:
    y_true, y_pred = np.asarray(y_true, float), np.asarray(y_pred, float)
    mask = y_true != 0
    if not mask.any():
        return float("nan")
    return float(100.0 * np.mean(np.abs((y_true[mask] - y_pred[mask]) / y_true[mask])))


def n_zero_excluded(y_true) -> int:
    return int(np.sum(np.asarray(y_true) == 0))
