import pandas as pd
import pytest

from forecast_core.ingestion import calendar

CFG = {
    "quincenas": {"dias_pago": [15, "ultimo_dia"], "ventana": {"dias_antes": 1, "dias_despues": 2}},
    "temporadas": [{"nombre": "diciembre", "meses": [12]}],
    "eventos_frontera": [
        {"id": "cierre", "tipo": "cierre", "inicio": "2015-08-19"},
        {"id": "parcial", "tipo": "reapertura_parcial", "inicio": "2016"},
        {"id": "total", "tipo": "reapertura", "inicio": "2016-06"},
    ],
}


def test_fechas_de_eventos_segun_precision() -> None:
    assert calendar.parse_event_date("2015-08-19") == pd.Timestamp("2015-08-19")
    assert calendar.parse_event_date("2019-02") == pd.Timestamp("2019-02-01")
    assert calendar.parse_event_date("2016") == pd.Timestamp("2016-01-01")
    with pytest.raises(ValueError, match="no válida"):
        calendar.parse_event_date("ayer")


def test_regimen_de_la_frontera() -> None:
    events = calendar.border_events(CFG)
    days = pd.DatetimeIndex(["2015-08-18", "2015-08-19", "2016-03-01", "2016-07-01"])
    assert calendar.border_regime(days, events).tolist() == [
        "abierta",
        "cerrada",
        "parcial",
        "abierta",
    ]


def test_festivos_de_colombia() -> None:
    hol = calendar.colombian_holidays([2025])
    assert pd.Timestamp("2025-12-25") in hol
    assert pd.Timestamp("2025-01-06") in hol  # Reyes Magos (lunes, Ley Emiliani)
    assert pd.Timestamp("2025-01-07") not in hol


def test_quincenas() -> None:
    days = pd.date_range("2026-01-13", "2026-02-03", freq="D")
    flags = dict(zip(days.strftime("%m-%d"), calendar.quincena_days(days, CFG), strict=True))
    assert all(flags[d] for d in ("01-14", "01-15", "01-17", "01-30", "01-31", "02-02"))
    assert not any(flags[d] for d in ("01-13", "01-18"))
    assert not flags["02-03"]


def test_variables_mensuales() -> None:
    idx = pd.date_range("2015-08-01", "2016-01-01", freq="MS")
    feats = calendar.calendar_features(idx, "MS", CFG)
    assert feats.loc["2015-09-01", "frontera_cerrada"] == 1.0
    assert 0 < feats.loc["2015-08-01", "frontera_cerrada"] < 1
    assert feats.loc["2015-12-01", "diciembre"] == 1
    assert feats.loc["2015-12-01", "festivos"] == 2  # 8 y 25 de diciembre
    assert feats.loc["2016-01-01", "frontera_parcial"] == 1.0


def test_variables_diarias() -> None:
    idx = pd.date_range("2025-12-24", "2025-12-26", freq="D")
    feats = calendar.calendar_features(idx, "D", CFG)
    assert feats["festivo"].tolist() == [0, 1, 0]
    with pytest.raises(ValueError, match="no soportada"):
        calendar.calendar_features(idx, "W", CFG)
