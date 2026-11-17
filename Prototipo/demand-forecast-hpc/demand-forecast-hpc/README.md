# Sistema de predicción de demanda – comercio minorista fronterizo (versión HPC)

Implementación alineada con la documentación (CRISP-DM + PCAM).
Las ventas son sintéticas mientras no haya ventas reales de comercios: **deben declararse como tales**.

## Cómo ejecutar (Windows / Linux / Mac)

1. Instalar Python 3.10 o superior (python.org). En Windows marcar "Add Python to PATH".
2. Descomprimir el zip y abrir una terminal (CMD / PowerShell) DENTRO de la carpeta `demand-forecast-hpc`.
3. Crear entorno e instalar lo básico:
   ```
   python -m venv .venv
   .venv\Scripts\activate          (Linux/Mac: source .venv/bin/activate)
   pip install numpy pandas scipy scikit-learn matplotlib
   ```
4. (Opcional, necesita internet) bajar la TRM real:
   ```
   python scripts/00_download_real_data.py
   ```
5. Ejecutar la Etapa 1:
   ```
   python scripts/01_eda_and_baseline.py
   ```
   Por defecto usa datos hasta AYER y pronostica los 14 días siguientes.
   Para fijar la fecha: `python scripts/01_eda_and_baseline.py --end 2026-11-06`

Resultados en `results/`: gráfico EDA, métricas de la línea base y pronóstico a futuro.

## Fuentes de datos reales identificadas

| Fuente | Qué da | Uso en el proyecto |
|---|---|---|
| datos.gov.co, dataset 32sa-8pi3 (TRM, Superfinanciera) | TRM diaria COP/USD | Variable exógena REAL (script 00) |
| DANE – Encuesta Mensual de Comercio (EMC) | Ventas reales minoristas mensuales, nacional y 6 departamentos | Contexto y validación de tendencia. NO incluye Norte de Santander como dominio y cubre empresas de 10+ empleados o ventas altas: no representa microempresas |
| Migración Colombia – Monitoreo de dinámicas migratorias | Flujos por paso fronterizo (informes mensuales) | Referencia para el aforo; no es una serie diaria lista para usar |
| Ventas transaccionales de MIPYMES | No existen públicas | Hay que conseguirlas con comerciantes (con autorización, Ley 1581) |

## Hoja de ruta

| Etapa | Qué se construye | Estado |
|---|---|---|
| 1 | Datos, EDA, RMSE/MAPE, origen móvil, línea base ingenua estacional, pronóstico a futuro | Hecha |
| 2 | SARIMA y Prophet (secuencial) | Siguiente |
| 3 | LSTM en PyTorch: CPU vs CUDA | Pendiente |
| 4 | OpenMP + MPI + diseño PCAM | Pendiente |
| 5 | Speedup, eficiencia, Amdahl, API y dashboard | Pendiente |

## Estructura

```
scripts/00_download_real_data.py  TRM real (datos.gov.co)
scripts/01_eda_and_baseline.py    Etapa 1
src/metrics.py          RMSE y MAPE
src/validation.py       Origen móvil
src/baselines.py        Ingenuo estacional
src/data_generation.py  Ventas sintéticas (+ TRM real opcional)
src/data_loader.py      CSV -> matriz (T días x N series) + reporte de calidad
```
