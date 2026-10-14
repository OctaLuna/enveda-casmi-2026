---
name: casmi-11-ensemble-reranker
description: Re-ranking final y ensamble para CASMI 2026 con LightGBM o XGBoost sobre candidatos de los tres pilares (A, B, C), optimizado para MRR@25 — diseño de features, generación out-of-fold, objetivo lambdarank, evaluación por clase y construcción del top-25 final. Úsala siempre que se combinen señales de varios pilares, se entrene el ranker, se discuta qué features usar, se calibre o se produzca la lista final de 25 SMILES por molécula.
---

# Ensamble y reranker

## Principio
Nunca dependas de un solo score (ni Tanimoto solo ni coseno solo). Entrena un **modelo de gradient boosting** que, para cada candidato generado por cualquiera de los tres pilares, combine todas las señales y produzca el orden final.

## Señales (features)
| Origen | Features |
|---|---|
| Pilar A (skill 06) | coseno DreaMS, entropía espectral, rank, nº de espectros coincidentes |
| Pilar B (skill 08) | Tanimoto blando, coseno de fingerprint, rank dentro de fórmula, nº de candidatos de fórmula, COSMIC (SIRIUS) |
| Masa/fórmula (skill 03) | error de masa (ppm), DBE, confianza de fórmula, discrepancia entre aductos |
| Pilar C (skill 09) | log-verosimilitud, frecuencia de muestreo, fuente del candidato |
| Cycle-consistency (skill 10) | similitud espectro simulado vs. observado (puede faltar) |
| Contexto | `n_spectra`, fuentes de la estructura (skill 05), flags de clase probable (p. ej. ¿hay hit espectral fuerte?) |

Las features ausentes (el candidato no vino de un pilar) deben ser **nulas explícitas** y acompañarse de flags `from_A/from_B/from_C`; LightGBM maneja NaN de forma nativa.

## Datos de entrenamiento: out-of-fold obligatorio
Los modelos de los pilares (DreaMS afinado, MIST, DiffMS) puntúan con confianza excesiva a las moléculas con las que entrenaron. Genera las features del ranker **solo** con predicciones de modelos que **no vieron** esa molécula (out-of-fold respecto al split de la skill 04). De lo contrario el ranker aprende a confiar en señales que en el test serán mucho más ruidosas.

- Unidad de grupo: cada `molecule_id` es un grupo de ranking; las filas son candidatos (unión de los tres pilares, deduplicada por InChIKey14).
- Etiqueta: 1 si el InChIKey14 del candidato coincide con el verdadero, 0 en otro caso. Si la estructura verdadera no está entre los candidatos, el grupo aporta solo ceros (es un fallo de recall, no del ranker; regístralo).

## Objetivo y métrica
La métrica real es MRR@25. MRR no es directamente diferenciable: usa un objetivo de ranking (`lambdarank` en LightGBM, `rank:ndcg`/`rank:pairwise` en XGBoost; `lambdarank_truncation_level`/`eval_at=[25]`), y **selecciona hiperparámetros, número de árboles y early stopping con MRR@25** calculado con la función de la skill 01 sobre los tres subsets de validación. No uses accuracy ni AUC como criterio de selección.

- Como hay una sola etiqueta positiva por grupo, la relevancia es binaria; revisa `label_gain` y `lambdarank_truncation_level` para enfatizar las primeras posiciones.
- Evalúa y reporta **por clase y por semilla** (skill 04). Considera un único ranker con flags de clase o rankers por clase; decide con el arnés.
- Fija semillas del modelo y registra `feature_importance`; desconfía de una feature que domine abrumadoramente (posible fuga).

## Construcción del top-25
1. Ordena por score del ranker.
2. **Deduplica por InChIKey14** y descarta SMILES inválidos (`dedupe_topk`, skill 01).
3. Si quedan < 25, rellena con los siguientes mejores candidatos de cualquier pilar; nunca envíes huecos si hay opciones.
4. Si el ensamble falla o se agota el tiempo para una molécula, aplica la lista de respaldo del Pilar A/B (skill 12).

## Verificación
- MRR@25 final por clase y por semilla; compara con cada pilar solo para demostrar que el ensamble aporta.
- Ablación por familia de features (quitar una familia a la vez) para saber qué señales justifican su costo de cómputo, especialmente `cc_*`.
- Comprobar que el ranking de test usa exactamente las mismas features y el mismo preprocesado que en validación.

