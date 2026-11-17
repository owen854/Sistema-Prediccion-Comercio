"""Descarga DATOS REALES disponibles públicamente y los guarda en data/.

1) TRM diaria (COP/USD) - Superintendencia Financiera, vía datos.gov.co
   Dataset 32sa-8pi3 (API Socrata). Requiere conexión a internet.

Uso:
    python scripts/00_download_real_data.py
    python scripts/00_download_real_data.py --desde 2023-01-01

NOTA: este script necesita internet. Si falla (firewall, sin red), descarga el
CSV a mano desde https://www.datos.gov.co/Econom-a-y-Finanzas/Tasa-de-Cambio-
Representativa-del-Mercado-TRM/32sa-8pi3 con el botón "Exportar" y guárdalo como
data/trm_real.csv con columnas: date,trm_cop_usd
"""
import argparse
import json
import urllib.parse
import urllib.request
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
URL = "https://www.datos.gov.co/resource/32sa-8pi3.json"


def fetch_trm(desde: str) -> pd.DataFrame:
    params = {
        "$where": f"vigenciadesde >= '{desde}T00:00:00.000'",
        "$order": "vigenciadesde ASC",
        "$limit": "50000",
    }
    url = URL + "?" + urllib.parse.urlencode(params, quote_via=urllib.parse.quote)
    with urllib.request.urlopen(url, timeout=60) as resp:
        rows = json.loads(resp.read().decode("utf-8"))
    if not rows:
        raise RuntimeError("La API respondió sin filas.")
    df = pd.DataFrame(rows)
    df["date"] = pd.to_datetime(df["vigenciadesde"]).dt.normalize()
    df["trm_cop_usd"] = df["valor"].astype(float)
    # Cada TRM rige desde 'vigenciadesde' hasta la siguiente: se rellena día a día
    s = (df.drop_duplicates("date", keep="last").set_index("date")["trm_cop_usd"])
    s = s.reindex(pd.date_range(s.index.min(), pd.Timestamp.today().normalize(), freq="D")).ffill()
    out = s.rename_axis("date").reset_index()
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--desde", default="2022-10-01")
    args = ap.parse_args()
    (ROOT / "data").mkdir(exist_ok=True)

    trm = fetch_trm(args.desde)
    path = ROOT / "data" / "trm_real.csv"
    trm.to_csv(path, index=False)
    print(f"TRM real guardada: {path}")
    print(f"  {len(trm)} días, de {trm['date'].min().date()} a {trm['date'].max().date()}")
    print(f"  último valor: {trm['trm_cop_usd'].iloc[-1]:,.2f} COP/USD")


if __name__ == "__main__":
    main()
