# Sprint 4: Ensamble Re-Ranker (LightGBM), Inferencia en Cascada (<9h) y Entrega Final
**Período**: 26 de Noviembre de 2026 – 14 de Diciembre de 2026 (Semanas 7 y 8)  
**Hitos Críticos**:
* **7 de Diciembre de 2026**: Cierre definitivo de inscripciones y fusiones de equipos en Kaggle.
* **14 de Diciembre de 2026 (11:59 PM UTC)**: Cierre definitivo de la competencia y selección de Notebooks finales.

---

## 1. Reparto Equitativo de Tareas

### Dev 1 (Octavio Luna): Lead de Ingeniería de Features para Ensamble y Validación Cruzada
* **Módulos**: `src/models/ensemble/feature_extractor.py`, `src/utils/cv_evaluator.py`
* **Tareas Asignadas**:
  1. `[DEV1-4.1]` Implementar extractor de features tabular para cada par `(query_spectrum, candidate_smiles)` cubriendo las 6 familias del Masterplan §7:
     - Similitud espectral: coseno DreaMS y entropía espectral (Pilar A).
     - Fingerprint estructural: similitud Tanimoto MIST y score de confianza COSMIC de SIRIUS / CSI:FingerID (Pilar B).
     - Parámetros estequiométricos: error de masa neutra ($\Delta ppm$), compatibilidad DBE y **score de confianza de la fórmula / ajuste isotópico** (mitigación de colapso §7).
     - Generación de novo y cycle-consistency: log-verosimilitud DiffMS/MSNovelist y similitud forward espectral simulada por CFM-ID / ICEBERG (Pilar C).
  2. `[DEV1-4.2]` Construir dataset de entrenamiento del re-ranker tabular a partir de predicciones *out-of-fold* (OOF) en las 3 clases.
  3. `[DEV1-4.3]` Diseñar arnés de evaluación con 3+ semillas aleatorias de split para evitar sobreajuste al Leaderboard público (~400 moléculas).

### Dev 2 (Leonardo Ibarra): Lead de Entrenamiento del Re-Ranker y Empaquetado Offline
* **Módulos**: `src/models/ensemble/lightgbm_ranker.py`, `src/utils/kaggle_packager.py`
* **Tareas Asignadas**:
  1. `[DEV2-4.1]` Implementar y entrenar modelo **LightGBM / XGBoost** con función objetivo tipo `lambdarank` optimizada directamente para maximizar **MRR@25**.
  2. `[DEV2-4.2]` Desarrollar scripts de exportación e inmutabilidad de modelos serializados (`.json` / `.txt` livianos para inferencia ultrarrápida sin dependencias pesadas).
  3. `[DEV2-4.3]` Empaquetar todos los artefactos de pesos (DreaMS, MIST, DiffMS, FAISS index, LightGBM model) en Kaggle Datasets con control estricto de hashes de integridad.

### Dev 3 (Joan Riveros): Lead de Orquestación en Cascada, Presupuesto de Cómputo (<9h) y Submission
* **Módulos**: `src/api/cascade_runner.py`, `src/api/submission.py`, `notebooks/kaggle_submission.ipynb`
* **Tareas Asignadas**:
  1. `[DEV3-4.1]` Implementar el orquestador en cascada en `src/api/cascade_runner.py`:
     - Paso 1: Clase 1 (Retrieval DreaMS) -> Si similitud $> 0.85$, resolver con Pilar A (< 0.2 s).
     - Paso 2: Si no, Clase 2 (MIST + Matching Fórmula) -> Si Tanimoto $> 0.75$, resolver con Pilar B (< 1.5 s).
     - Paso 3: Moléculas restantes -> Despachar a Clase 3 (DiffMS + Cycle-Consistency CFM-ID) con presupuesto controlado de 30-45 s por molécula.
  2. `[DEV3-4.2]` Monitorear y validar el presupuesto total de inferencia: asegurar que procesar las ~400 moléculas de test tome menos de **4.5 horas**, dejando un margen de seguridad del 50% frente al límite de 9 horas de Kaggle.
  3. `[DEV3-4.3]` Verificar exhaustivamente la integridad del archivo `submission.csv` final: formato, IDs completos, 25 SMILES delimitados por `;`.
  4. `[DEV3-4.4]` Congelar y ejecutar el Notebook final en Kaggle, verificar puntuación pública y seleccionar los 2 Notebooks finales definitivos antes del 14 de diciembre.

---

## 2. Cronograma de Cierre y Plan de Contingencia

| Fecha | Hito Operativo | Responsable Principal |
|---|---|---|
| **26 Nov - 02 Dic** | Extracción de features y entrenamiento de LightGBM Re-Ranker | Octavio Luna & Leonardo Ibarra |
| **03 Dic - 06 Dic** | Implementación y calibración del presupuesto en cascada (<9h) | Joan Riveros |
| **07 Dic** | **Límite de Fusiones en Kaggle** — Congelamiento final del equipo | Octavio, Leonardo, Joan |
| **08 Dic - 11 Dic** | Validación offline integral en entorno idéntico a Kaggle Notebooks | Octavio, Leonardo, Joan |
| **12 Dic - 13 Dic** | Generación de envíos finales de prueba y verificación de estabilidad de score | Joan Riveros |
| **14 Dic (11:59 PM UTC)** | **Selección de los 2 Notebooks finales en Kaggle** | Octavio, Leonardo, Joan |

---

## 3. Criterio de Aceptación Final (DoD)
- El pipeline en cascada ejecuta las ~400 moléculas de test en $\le 5$ horas en hardware estándar de Kaggle.
- El ensamble LightGBM mejora el MRR@25 global frente a cualquiera de los tres pilares de forma aislada.
- El notebook de Kaggle corre de forma 100% offline (sin internet) y genera un `submission.csv` estrictamente válido.
- Se documenta el reporte final comparativo de MRR@25 por clase: local vs. leaderboard público.

