"""Correlación cruzada con rezagos entre flujos fronterizos y ventas (RF-21; Patrón 4).

Convención: en el rezago ``k`` se correlaciona ``x_{t−k}`` con ``y_t``. Un rezago
positivo significa que ``x`` (flujos) antecede a ``y`` (ventas).

La banda aproximada de significancia es ±1,96/√n (Hyndman y Athanasopoulos, 2021).
Es aproximada porque las series tienen autocorrelación; se interpreta como indicio,
no como causalidad (limitación declarada en el informe).
"""

from __future__ import annotations

from collections.abc import Sequence
from typing import Literal

import numpy as np
import pandas as pd

Method = Literal["pct", "log"]


def yoy_change(series: pd.Series, periods: int = 12, method: Method = "log") -> pd.Series:
    """Variación anual: diferencia de logaritmos (``log``, en %) o porcentual (``pct``).

    El informe usó la diferencia de logaritmos: con ella se reproducen sus cifras
    (correlación 0,63 con la serie completa y 0,28 con rezago de 1 mes sin pandemia);
    con la variación porcentual no.
    """
    s = series.astype(float)
    if method == "pct":
        prev = s.shift(periods)
        out = (s / prev - 1.0) * 100.0
        out[prev == 0] = np.nan  # sin base de comparación (p. ej., frontera cerrada)
    elif method == "log":
        logs = pd.Series(np.log(s.where(s > 0).to_numpy()), index=s.index)
        out = (logs - logs.shift(periods)) * 100.0
    else:
        raise ValueError(f"Método desconocido: {method!r}.")
    return out.rename(f"{series.name}_var_anual")


def exclude_periods(series: pd.Series, periods: Sequence[tuple[str, str]]) -> pd.Series:
    """Pone en NaN los meses dentro de los periodos ``(inicio, fin)`` (formato ``AAAA-MM``)."""
    out = series.copy()
    for start, end in periods:
        mask = (out.index >= pd.Timestamp(f"{start}-01")) & (out.index <= pd.Timestamp(f"{end}-01"))
        out[mask] = np.nan
    return out


def cross_correlation(x: pd.Series, y: pd.Series, max_lag: int = 12) -> pd.DataFrame:
    """Correlación de Pearson entre ``x_{t−k}`` e ``y_t`` para k = −max_lag … max_lag."""
    rows = []
    for k in range(-max_lag, max_lag + 1):
        pair = pd.concat([x.shift(k), y], axis=1).dropna()
        n = len(pair)
        corr = float(pair.iloc[:, 0].corr(pair.iloc[:, 1])) if n > 2 else float("nan")
        rows.append({"rezago": k, "correlacion": corr, "n": n})
    return pd.DataFrame(rows)


def significance_band(n: int) -> float:
    return 1.96 / float(np.sqrt(n))


def strongest_lag(ccf: pd.DataFrame) -> pd.Series:
    """Fila con la mayor correlación (positiva)."""
    best: pd.Series = ccf.iloc[int(np.nanargmax(ccf["correlacion"].to_numpy()))]
    return best
