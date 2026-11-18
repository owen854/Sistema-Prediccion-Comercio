# Cuaderno del piloto LSTM

El cuaderno original de Colab con el que se generó el *Informe de evidencia OE1/OE2* no está disponible.

**Decisión del equipo (17/11/2026):** no se reemplaza con datos sintéticos. El piloto usó solo datos públicos
que el sistema ya tiene reales (índice de ventas de la EMC y entradas por Norte de Santander), así que se
**reconstruye a partir de la descripción del informe** (sección IV-B: 12 rezagos de la variación anual del
logaritmo de las ventas, variación anual de las entradas, mes en seno y coseno, una capa LSTM de 8 unidades,
ensamble de 5 redes entrenadas 400 épocas con Adam, origen móvil de jul-2024 a jun-2026 y 4 grupos de semillas).

La reconstrucción es la historia **HU-15** de la Fase 2 (`configs/experiments/e04_lstm_publico.yaml`).
Si en algún momento aparece el cuaderno original, se guarda aquí para comparar.
