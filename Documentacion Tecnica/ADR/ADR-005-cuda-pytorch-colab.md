# ADR-005: CUDA mediante PyTorch, ejecutado en Google Colab

- **Estado:** Aceptada
- **Fecha:** 2026-11-17

## Contexto

El OE3 exige entrenar modelos de deep learning con CUDA. El equipo de desarrollo tiene una GPU Intel Iris Xe, sin soporte CUDA. El piloto de la LSTM del informe se programó en NumPy y corrió en CPU.

## Decisión

- La LSTM se implementa en **PyTorch**, que usa **CUDA y cuDNN** cuando hay una GPU NVIDIA.
- Los entrenamientos y benchmarks de GPU se ejecutan en **Google Colab** (GPU T4) con el cuaderno `Codigo Fuente/infra/gpu_remota/run_cuda_experiments.ipynb`, que clona el repositorio público e instala el paquete.
- La aceleración se calcula comparando CPU y GPU **en la misma sesión de Colab**.
- **Kaggle** (hasta 2 GPU T4) y el laboratorio de la universidad son alternativas si Colab no asigna GPU o se necesita más de una.

## Alternativas consideradas

| Alternativa | Motivo de descarte |
|---|---|
| Núcleos CUDA escritos a mano en C++ | Mucho más trabajo y riesgo; PyTorch ya ejecuta la LSTM sobre cuDNN, que es CUDA. Se puede agregar un núcleo propio como extensión opcional. |
| Comprar o alquilar una GPU | Costo, contrario a la justificación práctica. |
| Renunciar a CUDA | Incumple el OE3. |

## Consecuencias

- El código no depende de dónde corra: detecta el dispositivo y usa CPU si no hay GPU (RNF-13).
- Las limitaciones de Colab (sesiones, GPU no garantizada, almacenamiento temporal) se manejan con puntos de control y resultados en Drive.
- CUDA y cuDNN son gratuitos pero con licencia propietaria de NVIDIA; se declara en el inventario de licencias.
