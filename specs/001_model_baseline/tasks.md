# Tareas Atómicas SDD: 001_model_baseline
## Desglose de Tareas (<30 min) para Dev 1, Dev 2 y Dev 3

> **ID de Tareas**: `TASKS-001`  
> **Feature**: Pipeline Base y Baseline de Recuperación Espectral  
> **Regla de Cierre**: Prohibido marcar `[x]` sin la ejecución previa y exitosa de la prueba unitaria correspondiente (`pytest tests/... -v`).

---

## Bloque 1: Infraestructura de Reproducibilidad y Métricas (Días 1-2)

- [x] `[DEV1-T1.1]` [RF: REQ-UBI-04] Implementar módulo `src/utils/reproducibility.py` con `set_seed(seed: int = 42)` asegurando determinismo en random, numpy y torch.  
  *Estimación*: 20 min | *Dependencias*: Ninguna | *DoD*: `test_set_seed_determinism` ejecutado y passing en `tests/test_reproducibility.py`.

- [x] `[DEV1-T1.2]` [RF: REQ-UBI-02] Implementar `src/utils/metrics.py` con `smiles_to_inchikey14()` y canonicalizador tautomérico `rdMolStandardize.TautomerEnumerator`.  
  *Estimación*: 30 min | *Dependencias*: Ninguna | *DoD*: `test_smiles_to_inchikey14_valid` passing con SMILES de prueba.

- [x] `[DEV1-T1.3]` [RF: REQ-UBI-03] Implementar función `calculate_mrr_at_25()` en `src/utils/metrics.py` según la fórmula oficial de Kaggle.  
  *Estimación*: 25 min | *Dependencias*: T1.2 | *DoD*: `test_calculate_mrr_at_25_*` pasando casos rank 1, rank 2, rank 4, y $>25$.

- [x] `[DEV3-T1.4]` [RF: REQ-ERR-03, REQ-STA-01] Implementar generador y validador de `submission.csv` en `src/api/submission.py` (`write_submission_csv` y `validate_submission_csv`).  
  *Estimación*: 25 min | *Dependencias*: Ninguna | *DoD*: `test_write_and_validate_submission_csv` passing.

---

## Bloque 2: Modelo de Datos Espectrales y Limpieza (Días 3-5)

- [x] `[DEV1-T2.1]` [RF: REQ-UBI-01] Definir clase de datos `SpectrumRecord` en `src/data/spectrum_parser.py` con validación estricta de longitudes de arreglos $m/z$ e intensidades.  
  *Estimación*: 20 min | *Dependencias*: Ninguna | *DoD*: `test_spectrum_record_creation` y `test_spectrum_record_length_mismatch` passing.

- [x] `[DEV1-T2.2]` [RF: REQ-EVT-02] Implementar método `filter_noise_peaks(threshold=0.01)` en `SpectrumRecord` para descartar picos ruidosos $<1\%$ del pico base.  
  *Estimación*: 20 min | *Dependencias*: T2.1 | *DoD*: `test_filter_noise_peaks` passing.

- [x] `[DEV1-T2.3]` [RF: REQ-EVT-01] Implementar método `filter_precursor_overhang(mass_tolerance_da=2.0)` en `SpectrumRecord` para eliminar picos superiores al precursor.  
  *Estimación*: 20 min | *Dependencias*: T2.1 | *DoD*: `test_filter_precursor_overhang` passing.

- [x] `[DEV1-T2.4]` [RF: REQ-OPT-01, REQ-EVT-07] Implementar normalizador de masa neutra a partir del campo `adduct` (`[M+H]+`, `[M-H]-`, `[M+Na]+`, etc.) en `src/data/adduct_normalizer.py`.  
  *Estimación*: 30 min | *Dependencias*: T2.1 | *DoD*: Test unitario con tabla de aductos Bruker timsTOF passing.

- [x] `[DEV1-T2.5]` [RF: REQ-EVT-06] Implementar algoritmo de deisotopado explícito colapsando isotopos (+1, +2 Da) en `src/data/deisotoper.py`.  
  *Estimación*: 30 min | *Dependencias*: T2.1 | *DoD*: Test unitario con pares isotópicos sintéticos passing.

- [x] `[DEV1-T2.6]` [RF: REQ-STA-01, REQ-EVT-08] Adaptar el cargador por lotes al esquema oficial: `inchikey14`/`normalized_smiles` en train y `molecule_id`/`spectrum_id` en test; sintetizar IDs de espectro estables para train.
  *Estimación*: 30 min | *Dependencias*: T2.1 | *DoD*: Tests de lectura para ambos esquemas passing y lectura real de los metadatos oficiales sin cargar arreglos de picos.

---

## Bloque 3: Generador de Splits Anti-Leakage (Días 6-7)

- [x] `[DEV1-T3.1]` [RF: REQ-EVT-03] Particionar por `molecule_id` en `src/data/splitter.py`; Val-Clase2/3 quedan fuera de train y la consulta retenida de Val-Clase1 se excluye de la biblioteca.
  *Estimación*: 30 min | *Dependencias*: T2.6 | *DoD*: Test de pertenencia por molécula y exclusión del espectro de consulta passing.

- [x] `[DEV1-T3.2]` [RF: REQ-EVT-04] Canonicalizar tautómeros, agrupar scaffolds Murcko y excluir scaffolds vecinos por ECFP4/Tanimoto para aislar `Val-Clase3` de train.
  *Estimación*: 30 min | *Dependencias*: T3.1 | *DoD*: Tests de tautómeros equivalentes, equivalencia de similitud exacta con RDKit y distancia media de cada molécula Val-Clase3 a su vecino Train más cercano $> 0.60$; búsqueda masiva delegada a `BulkTanimotoSimilarity` nativo.

- [x] `[DEV1-T3.3]` [RF: REQ-UBI-04, REQ-EVT-04] Generar manifiestos de validación para las semillas `42`, `1337` y `2026` desde `train.parquet`, leyendo metadatos por lotes y guardando JSON compactos en `data/splits/`.
  *Estimación*: 25 min | *Dependencias*: T3.2 | *DoD*: Los tres archivos contienen pertenencia por molécula, consultas retenidas de Clase 1, conteos, semilla y SHA-256 del train; cada uno es menor a 25 MiB.

- [x] `[DEV1-T3.4]` Validar manifiestos con el hook H22 y permitir versionar únicamente los tres JSON esperados.
  *Estimación*: 20 min | *Dependencias*: T3.3 | *DoD*: Selftest cubre manifiestos válidos, fuga, archivo ausente, semilla incorrecta y archivo mayor a 25 MiB; ningún Parquet crudo queda permitido en Git.

---

## Bloque 4: Motor de Recuperación Baseline y Submisión (Días 8-10)

- [x] `[DEV2-T4.1]` [RF: REQ-EVT-05] Implementar motor de coincidencia `BaselineSpectralMatcher` en `src/models/baseline_agent.py` basado en ventana de masa de precursor.  
  *Estimación*: 25 min | *Dependencias*: T2.1 | *DoD*: `test_baseline_matcher_fit_and_predict` passing.

- [ ] `[DEV2-T4.2]` [RF: REQ-OPT-02] Integrar similitud de coseno y entropía espectral básica (`matchms`) en `src/models/retrieval/spectral_similarity.py`.  
  *Estimación*: 30 min | *Dependencias*: T4.1 | *DoD*: Test comparativo de similitud de espectros sintéticos passing.

- [ ] `[DEV3-T4.3]` [RF: REQ-UBI-03] Implementar script ejecutable de benchmarking `scripts/evaluate_baseline.py` que cargue los splits, evalúe en las 3 clases y reporte MRR@25.  
  *Estimación*: 30 min | *Dependencias*: T1.3, T3.3, T4.1 | *DoD*: Reporte generado en consola y exportado a markdown con los 3 scores.

- [ ] `[DEV3-T4.4]` [RF: REQ-ERR-03, REQ-STA-01] Implementar pipeline completo de generación de `submission.csv` para `test.parquet` usando el baseline y validar formato final.  
  *Estimación*: 25 min | *Dependencias*: T1.4, T4.1 | *DoD*: Archivo `submission.csv` generado y validado con `validate_submission_csv()`.
