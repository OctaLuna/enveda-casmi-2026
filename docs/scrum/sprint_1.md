# Sprint 1: Preparación de Datos, Arnés Anti-Leakage y Pipeline Baseline
**Período**: 14 de Octubre de 2026 – 28 de Octubre de 2026 (Semanas 1 y 2)  
**Meta del Sprint**: Lograr un pipeline de extremo a extremo completamente testeado: ingestión de espectros con limpieza química, split estructural simulando las 3 clases, estandarización InChIKey14 exacta, métrica local MRR@25 y primer baseline de recuperación con generación de `submission.csv`.

---

## 1. Reparto Equitativo de Tareas

### Dev 1 (Octavio Luna): Lead de Datos, Preprocesamiento y Métrica InChIKey14
* **Módulos**: `src/data/`, `src/utils/metrics.py`, `src/utils/reproducibility.py`
* **Tareas Asignadas**:
  1. `[DEV1-1.1]` Implementar `src/utils/reproducibility.py` con `set_seed()` fijando Python, NumPy y PyTorch. *(Día 1)*
  2. `[DEV1-1.2]` Implementar `src/utils/metrics.py` con canonicalización tautomérica exacta (`rdMolStandardize.TautomerEnumerator`), generación de `InChIKey14` y cálculo de `calculate_mrr_at_25()`. *(Días 2-3)*
  3. `[DEV1-1.3]` Implementar cargador eficiente de `train.parquet` y `test.parquet` en `src/data/loader.py` con validación de tipos PyArrow/Polars. *(Días 4-5)*
  4. `[DEV1-1.4]` Desarrollar pipeline de limpieza de espectros en `src/data/preprocessor.py`:
     - Filtro de intensidad relativa (<1-2% pico base).
     - Filtro de precursores ($m/z > \text{precursor} + 2.0\text{ Da}$).
     - Deisotopado explícito colapsando isotopos (+1, +2 Da).
     - Transformación de intensidades (sqrt/log) y cálculo de masa neutra según aducto. *(Días 6-8)*
  5. `[DEV1-1.5]` Implementar generador de splits estructurales en `src/data/splitter.py`: partición por `molecule_id` con clustering de scaffold Murcko / MCES, generando los 3 subsets: `Val-Clase1`, `Val-Clase2`, `Val-Clase3` con 3 semillas. *(Días 9-10)*

### Dev 2 (Leonardo Ibarra): Lead de Motores de Búsqueda y Baseline Espectral
* **Módulos**: `src/models/retrieval/base.py`, `src/models/retrieval/cosine_baseline.py`, `src/models/candidates/`
* **Tareas Asignadas**:
  1. `[DEV2-1.1]` Definir contratos de datos compartidos `SpectrumRecord` y `CandidatePrediction` en `src/models/interfaces.py` para desacoplar dependencias. *(Día 1)*
  2. `[DEV2-1.2]` Implementar cálculo de similitud espectral por coseno clásico y entropía espectral (`Li et al., 2021`) con `matchms` en `src/models/retrieval/spectral_similarity.py`. *(Días 3-5)*
  3. `[DEV2-1.3]` Desarrollar indexador de búsqueda baseline en memoria sobre espectros de entrenamiento limpios. *(Días 6-8)*
  4. `[DEV2-1.4]` Ejecutar benchmark del baseline de coseno sobre `Val-Clase1` reportando MRR@25 inicial. *(Días 9-10)*

### Dev 3 (Joan Riveros): Lead de Pipeline de Inferencia, Submisión y Validación
* **Módulos**: `src/api/submission.py`, `src/models/baseline_agent.py`, `tests/`
* **Tareas Asignadas**:
  1. `[DEV3-1.1]` Implementar formateador y validador estricto de `submission.csv` en `src/api/submission.py`: validación de hasta 25 SMILES separados por `;`, sin nulos, y verificación de que todos los `molecule_id` de test estén presentes. *(Días 2-3)*
  2. `[DEV3-1.2]` Desarrollar orquestador baseline de extremo a extremo que conecta la ingesta de Octavio, la búsqueda espectral de Leonardo y el formateador de salida. *(Días 6-8)*
  3. `[DEV3-1.3]` Construir script de benchmarking comparativo que evalúa el baseline en los 3 subsets (`Val-Clase1`, `Val-Clase2`, `Val-Clase3`) y exporta reporte en markdown. *(Día 9)*
  4. `[DEV3-1.4]` Preparar el Notebook base de Kaggle con ejecución offline verificada (<15 min para el baseline) y generar el primer submission oficial de calibración. *(Día 10)*

---

## 2. Mapa de Dependencias y Mitigación de Bloqueos

```
[Día 1] Dev 1: set_seed() & Dev 2: interfaces.py  (Sin dependencias previas)
          |
[Día 2-3] Dev 1 entrega metrics.py (MRR@25 + InChIKey14)
          |===========================================+
          |                                           |
          v                                           v
[Día 4-5] Dev 2 usa metrics.py             Dev 3 implementa submission.py
          para spectral_similarity.py        y validador de formato Kaggle
          |                                           |
          +---------------------+---------------------+
                                |
[Día 6-8] Dev 1 entrega preprocessor.py y splits de datos
          |
          v
[Día 9-10] Dev 2 corre baseline en Val-Clase1  <--->  Dev 3 ensambla submission.csv
                                                       y genera primer envío Kaggle
```

---

## 3. Criterio de Aceptación del Sprint (DoD)
- Cobertura de tests unitarios $>85\%$ en `src/data/` y `src/utils/`.
- Preprocesador genera espectros limpios y reproducibles para ~2M de filas sin memory leaks.
- Split estructural genera los 3 subsets disjuntos por `molecule_id`.
- Submission baseline corre en Kaggle offline y devuelve un score público mayor a 0.000.

