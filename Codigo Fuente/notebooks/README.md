# Cuadernos

Análisis reproducibles por objetivo específico. Los cuadernos **no contienen lógica propia**: llaman funciones de `forecast_core`, para que cada figura y tabla del informe se regenere desde el código (RNF-28).

| Cuaderno | Objetivo | Fase |
|---|---|---|
| `01_patrones_consumo_OE1.ipynb` | Reproducir y ampliar los patrones de consumo del informe (Tablas III y IV, Figuras 1 a 5) | Fase 1 |
| `02_seleccion_modelos_OE2.ipynb` | Comparación de modelos y réplica del piloto LSTM (Tabla VII) | Fase 2 |
| `03_rendimiento_paralelo_OE3.ipynb` | Tiempos, aceleración, eficiencia y Amdahl con OpenMP, MPI y CUDA | Fase 3 |
| `04_validacion_OE4.ipynb` | Validación final y simulación de inventario | Fase 5 |
| `legacy/` | Cuaderno de Colab del piloto LSTM del informe (referencia) | Fase 0 |

Para usarlos en WSL: `cd backend && uv run --with jupyterlab jupyter lab ../notebooks`.
