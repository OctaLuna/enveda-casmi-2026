# Workflow: /new-experiment
**Propósito**: Inicializar de forma ordenada y reproducible un nuevo experimento de modelado o extracción de features.

## Pasos de Ejecución:
1. **Creación de Rama de Experimento**:
   ```bash
   git checkout develop
   git pull origin develop
   git checkout -b exp/<nombre-descriptivo>
   ```
2. **Definición de Semillas Deterministas**:
   Asegurar que el experimento se ejecute sobre al menos 3 semillas (`[42, 1337, 2026]`) usando `set_seed()`.
3. **Registro en EXPERIMENTS.md**:
   Añadir la fila preliminar en la bitácora con la fecha, hipótesis técnica y commit inicial.
4. **Almacenamiento de Métricas**:
   Asegurar que los resultados de MRR@25 por clase se guarden en `reports/latest_metrics.json` para que el hook `H50` los capture automáticamente.
