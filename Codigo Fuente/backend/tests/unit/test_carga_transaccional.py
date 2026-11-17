import pandas as pd
import pytest

from forecast_core.ingestion.transactional import (
    SalesValidationError,
    read_sales_file,
    validate_sales,
)
from forecast_core.privacy.anonymization import (
    drop_personal_columns,
    pseudonymize,
    pseudonymize_column,
)

CSV = (
    "Fecha;Producto;Unidades;Categoría;Sucursal;Nombre cliente;Cédula\n"
    "15/01/2026;arroz-500;12;Canasta;Centro;Ana Pérez;123\n"
    "2026-01-16;ARROZ-500;3,5;Canasta;Centro;Luis Gómez;456\n"
)


def test_lee_csv_con_punto_y_coma_alias_y_formatos_de_fecha() -> None:
    raw = read_sales_file(CSV.encode("utf-8"), "ventas.csv")
    clean, removed = drop_personal_columns(raw)
    assert set(removed) == {"Nombre cliente", "Cédula"}
    sales = validate_sales(clean)
    assert sales["date"].dt.strftime("%Y-%m-%d").tolist() == ["2026-01-15", "2026-01-16"]
    assert sales["series_id"].tolist() == ["ARROZ-500", "ARROZ-500"]
    assert sales["units"].tolist() == [12.0, 3.5]
    assert sales["category"].tolist() == ["Canasta", "Canasta"]


def test_lee_excel(tmp_path: object) -> None:
    import io

    buf = io.BytesIO()
    pd.DataFrame({"fecha": ["2026-01-15"], "codigo_producto": ["A1"], "cantidad": [4]}).to_excel(
        buf, index=False
    )
    sales = validate_sales(read_sales_file(buf.getvalue(), "ventas.xlsx"))
    assert sales["units"].tolist() == [4.0]


def test_rechaza_columnas_faltantes_y_filas_invalidas() -> None:
    with pytest.raises(SalesValidationError) as e1:
        validate_sales(pd.DataFrame({"fecha": ["2026-01-01"], "cantidad": ["1"]}))
    assert e1.value.problemas[0].columna == "codigo_producto"

    df = pd.DataFrame(
        {
            "fecha": ["2026-01-01", "31/02/2026"],
            "codigo_producto": ["A", ""],
            "cantidad": ["-1", "x"],
        }
    )
    with pytest.raises(SalesValidationError) as e2:
        validate_sales(df)
    filas = {(p.fila, p.columna) for p in e2.value.problemas}
    assert (3, "fecha") in filas  # 31 de febrero no existe
    assert {(2, "cantidad"), (3, "cantidad")} <= filas
    assert (3, "codigo_producto") in filas


def test_formato_no_soportado() -> None:
    with pytest.raises(SalesValidationError, match="no soportado"):
        read_sales_file(b"x", "ventas.pdf")


def test_seudonimo_estable_y_dependiente_de_la_clave() -> None:
    a = pseudonymize("Sucursal Centro", b"k1", "PV")
    assert a == pseudonymize("  sucursal  centro ", b"k1", "PV")
    assert a != pseudonymize("Sucursal Centro", b"k2", "PV")
    assert a.startswith("PV")
    assert len(a) == 14
    with pytest.raises(ValueError, match="vacía"):
        pseudonymize("x", b"")
    df = pseudonymize_column(pd.DataFrame({"store": ["Centro", None]}), "store", b"k1", "PV")
    assert df["store"].iloc[0].startswith("PV")
    assert pd.isna(df["store"].iloc[1])  # un faltante sigue faltante
