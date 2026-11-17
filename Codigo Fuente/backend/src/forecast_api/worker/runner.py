"""Bucle del worker.

Algoritmo previsto:
1. Tomar el siguiente trabajo pendiente con ``SELECT ... FOR UPDATE SKIP LOCKED``.
2. Marcarlo ``en_curso`` y lanzar el pipeline (``mpiexec -n p python -m ...`` si la
   estrategia es MPI).
3. Guardar progreso y registros; importar resultados; marcar ``ok`` o ``fallido``.

Requerimientos: RF-64, RNF-12.
Fase de implementación: Fase 4 (Sprint 2).
"""
