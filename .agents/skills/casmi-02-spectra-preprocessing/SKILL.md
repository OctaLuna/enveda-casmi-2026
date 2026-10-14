---
name: casmi-02-spectra-preprocessing
description: Preprocesamiento de espectros MS/MS para Enveda CASMI 2026 — filtro de intensidad, filtro de precursor, control de densidad, transformación sqrt/log, deisotopado explícito, deduplicación de espectros y carga eficiente de train.parquet/test.parquet (campos ms2_mzs, ms2_normalized_intensities, precursor_mz, adduct, collision_energy_ev). Úsala siempre que se limpien, normalicen, binneen, embedan o carguen espectros, o se prepare cualquier entrada para DreaMS, MIST, DiffMS o matchms.
---

# Preprocesamiento de espectros

## Datos
- `train.parquet`: ~2 M espectros, ~275 k estructuras únicas (GNPS, MassBank, MoNA, RIKEN, Enveda-180).
- `test.parquet`: ~1,500 espectros de ~400 moléculas, Bruker timsTOF, 157–1,159 Da.
- Campos: `molecule_id`, `spectrum_id`, `ms2_mzs`, `ms2_normalized_intensities` (pico base = 1.0), `precursor_mz`, `adduct`, `collision_energy_ev`, `label` (SMILES, solo train).
- Una molécula puede tener varios espectros (distintos aductos/energías de colisión).

## Pipeline base (en este orden)
1. **Intensidad mínima:** eliminar picos < 1–2 % del pico base (parametrizar; el valor se ajusta con validación).
2. **Filtro de precursor:** descartar fragmentos con m/z > `precursor_mz` + ~2 Da (tolerancia isotópica).
3. **Deisotopado explícito:** colapsar picos +1/+2 Da a su especie monoisotópica **antes** de cualquier binning o embedding. Es un paso obligatorio del masterplan.
4. **Control de densidad:** descartar espectros con < 5 picos; en espectros densos conservar los Top-N más informativos o filtrar por ventanas de masa (p. ej. top-k por ventana de 50 Da).
5. **Transformación de intensidades:** raíz cuadrada o log para que los picos dominantes no distorsionen el entrenamiento. Renormaliza tras transformar.
6. **Deduplicación:** quitar espectros casi idénticos (misma molécula, mismo aducto, similitud coseno ≈ 1) para no sobre-representar moléculas muy medidas.

## Buenas prácticas
- Aplica **exactamente la misma función** a train, validación y test (una sola función `preprocess_spectrum`); un desajuste silencioso entre train y test es una fuente clásica de pérdida de rendimiento.
- Conserva una columna `n_peaks_after` y un flag de calidad; la fusión multi-espectro (skill 07) los usa como pesos.
- Los parquets son grandes: lee por columnas y por *row groups* con `pyarrow`, procesa en lotes y guarda el resultado en parquet intermedio versionado. Evita convertir 2 M arreglos a objetos Python de una vez.
- `matchms` ofrece filtros estándar (`normalize_intensities`, `select_by_relative_intensity`, `select_by_mz`, `require_minimum_number_of_peaks`) y es válido para esta fase; verifica los nombres exactos en la versión instalada.
- La conversión a masa neutra por aducto **no** se hace aquí: ver skill 03.
- Cada decisión de umbral se justifica con el MRR@25 del arnés de validación (skill 04), no por intuición.

## Verificación
- Histograma de nº de picos antes/después y fracción de espectros descartados por split y por tipo de aducto.
- Comprobar que ningún espectro de test quede vacío; si ocurre, aplicar una regla de respaldo (relajar umbrales) en vez de descartarlo, porque cada molécula del test debe tener respuesta.
