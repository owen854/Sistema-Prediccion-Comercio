"""Calendario de festivos, quincenas, temporadas y eventos de frontera (RF-05).

La configuración está en ``configs/calendar_events.yaml``. Los eventos de frontera
definen un régimen por fecha: ``abierta``, ``cerrada`` o ``parcial``.
"""

from __future__ import annotations

import re
from collections.abc import Iterable, Mapping
from typing import Any

import holidays
import numpy as np
import pandas as pd

from forecast_core.config import load_yaml

CONFIG_PATH = "configs/calendar_events.yaml"
EVENT_DATE = re.compile(r"^\d{4}(-\d{2}(-\d{2})?)?$")
REGIME_BY_EVENT = {"cierre": "cerrada", "reapertura_parcial": "parcial", "reapertura": "abierta"}


def load_calendar_config(path: str = CONFIG_PATH) -> dict[str, Any]:
    return load_yaml(path)


def colombian_holidays(years: Iterable[int]) -> pd.DatetimeIndex:
    """Festivos oficiales de Colombia (Ley Emiliani incluida) para los años dados."""
    days = holidays.country_holidays("CO", years=list(years))
    return pd.DatetimeIndex(sorted(pd.Timestamp(d) for d in days))


def parse_event_date(value: str) -> pd.Timestamp:
    """``"2015-08-19"`` → ese día; ``"2019-02"`` → primer día del mes; ``"2016"`` → 1 de enero."""
    text = str(value).strip()
    if not EVENT_DATE.match(text):
        raise ValueError(f"Fecha de evento no válida: {value!r} (use AAAA, AAAA-MM o AAAA-MM-DD).")
    parts = text.split("-")
    if len(parts) == 3:
        return pd.Timestamp(text)
    if len(parts) == 2:
        return pd.Timestamp(f"{text}-01")
    return pd.Timestamp(f"{text}-01-01")


def border_events(config: Mapping[str, Any]) -> pd.DataFrame:
    """Eventos de frontera ordenados por fecha, con su régimen resultante."""
    records = []
    for ev in config.get("eventos_frontera", []):
        tipo = ev["tipo"]
        if tipo not in REGIME_BY_EVENT:
            raise ValueError(f"Tipo de evento desconocido: {tipo!r}.")
        records.append(
            {
                "id": ev["id"],
                "tipo": tipo,
                "inicio": parse_event_date(ev["inicio"]),
                "precision": ev.get("precision", "dia"),
                "verificar": bool(ev.get("verificar", False)),
                "regimen": REGIME_BY_EVENT[tipo],
                "fuente": ev.get("fuente", ""),
            }
        )
    return pd.DataFrame.from_records(records).sort_values("inicio", ignore_index=True)


def border_regime(dates: pd.DatetimeIndex, events: pd.DataFrame) -> pd.Series:
    """Régimen de la frontera en cada fecha (abierta antes del primer evento)."""
    values = np.full(len(dates), "abierta", dtype=object)
    for inicio, regimen in zip(
        pd.DatetimeIndex(events["inicio"]), events["regimen"].astype(str), strict=True
    ):
        values[np.asarray(dates >= inicio)] = regimen
    return pd.Series(values, index=dates, name="regimen_frontera")


def quincena_days(dates: pd.DatetimeIndex, config: Mapping[str, Any]) -> np.ndarray:
    """Marca los días cercanos a los días de pago (supuesto configurable)."""
    q = config.get("quincenas", {})
    antes = int(q.get("ventana", {}).get("dias_antes", 1))
    despues = int(q.get("ventana", {}).get("dias_despues", 2))
    flags = np.zeros(len(dates), dtype=bool)
    for dia in q.get("dias_pago", [15, "ultimo_dia"]):
        if dia == "ultimo_dia":
            pago = dates + pd.offsets.MonthEnd(0)
        else:
            pago = pd.DatetimeIndex([d.replace(day=min(int(dia), d.days_in_month)) for d in dates])
        delta = (dates - pago).days.to_numpy()
        flags |= (delta >= -antes) & (delta <= despues)
        if dia == "ultimo_dia":  # la ventana después del fin de mes cae en el mes siguiente
            prev_end = dates - pd.offsets.MonthBegin(1) - pd.Timedelta(days=1)
            delta_prev = (dates - prev_end).days.to_numpy()
            flags |= (delta_prev > 0) & (delta_prev <= despues) & (dates.day <= despues)
    return flags


def calendar_features(
    index: pd.DatetimeIndex, freq: str, config: Mapping[str, Any] | None = None
) -> pd.DataFrame:
    """Variables de calendario por periodo para frecuencia diaria (``"D"``) o mensual (``"MS"``)."""
    cfg = config if config is not None else load_calendar_config()
    events = border_events(cfg)
    out = pd.DataFrame(index=index)
    month = index.month.to_numpy()
    out["mes_seno"] = np.sin(2 * np.pi * month / 12)
    out["mes_coseno"] = np.cos(2 * np.pi * month / 12)
    temporada_meses = {m for t in cfg.get("temporadas", []) for m in t.get("meses", [])}
    out["diciembre"] = np.isin(month, sorted(temporada_meses or {12})).astype(int)

    if freq == "D":
        dow = index.day_of_week.to_numpy()
        out["dia_semana_seno"] = np.sin(2 * np.pi * dow / 7)
        out["dia_semana_coseno"] = np.cos(2 * np.pi * dow / 7)
        hol = colombian_holidays(range(index.min().year, index.max().year + 1))
        out["festivo"] = index.isin(hol).astype(int)
        out["quincena"] = quincena_days(index, cfg).astype(int)
        regime = border_regime(index, events)
        out["frontera_cerrada"] = (regime == "cerrada").astype(int)
        out["frontera_parcial"] = (regime == "parcial").astype(int)
        return out

    if freq in ("MS", "M"):
        days = pd.date_range(index.min(), index.max() + pd.offsets.MonthEnd(0), freq="D")
        hol = colombian_holidays(range(days.min().year, days.max().year + 1))
        regime = border_regime(days, events)
        daily = pd.DataFrame(
            {
                "festivo": days.isin(hol).astype(int),
                "frontera_cerrada": (regime == "cerrada").astype(float),
                "frontera_parcial": (regime == "parcial").astype(float),
            },
            index=days,
        )
        monthly = daily.groupby(days.to_period("M")).agg(
            festivos=("festivo", "sum"),
            frontera_cerrada=("frontera_cerrada", "mean"),
            frontera_parcial=("frontera_parcial", "mean"),
        )
        monthly.index = pd.PeriodIndex(monthly.index).to_timestamp()
        return out.join(monthly.reindex(index))

    raise ValueError(f"Frecuencia no soportada: {freq!r} (use 'D' o 'MS').")
