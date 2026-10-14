---
name: casmi-08-pillar-b-fingerprint
description: Pilar B de CASMI 2026 (Clase 2, estructura conocida sin espectro público) — predicción de fingerprint molecular desde el espectro con MIST, matching por Tanimoto contra el universo de candidatos filtrado por fórmula, y señal complementaria SIRIUS 6 / CSI:FingerID con score COSMIC. Úsala siempre que se prediga un fingerprint, se rankeen candidatos por similitud de fingerprint, se entrene o afine MIST, o se integre SIRIUS/CSI:FingerID.
---

# Pilar B — Fingerprint + matching por fórmula

## Flujo completo
1. **Fórmula:** masa neutra por aducto + estimación de fórmula con filtros DBE/valencia (skill 03). Usa las top-k fórmulas con su confianza, no solo la primera.
2. **Fingerprint desde el espectro con MIST** — el predictor neuronal de fingerprint principal. Es la pieza de mayor apalancamiento del proyecto: el mismo componente alimenta el decodificador del Pilar C (DiffMS), de modo que mejorarlo beneficia a B y C a la vez.
3. **Universo de candidatos** de la fórmula (skill 05).
4. **Ranking por Tanimoto** entre el fingerprint predicho y el real de cada candidato.
5. **Señal complementaria:** SIRIUS 6 / CSI:FingerID con su score de confianza **COSMIC** (señal independiente de MIST). Es un complemento del ensamble, no un sustituto.

> **Antes de escribir código:** consulta el README del repositorio de MIST (samgoldman97/mist) para el formato de entrada, el tipo de fingerprint que predice (bits y definición), cómo entrenar/afinar y cómo cargar pesos offline. Usa **la misma definición de fingerprint** para los candidatos reales (skill 05); si difiere, el Tanimoto carece de sentido. Para SIRIUS verifica el modo de uso local (CLI), sus requisitos (Java), la licencia y si puede empaquetarse en un dataset de Kaggle sin internet.

## Tanimoto con fingerprint predicho
MIST produce probabilidades por bit, no bits binarios. Usa el Tanimoto "blando":
`T = Σ(p·c) / (Σp + Σc − Σp·c)` con `p` = probabilidad predicha y `c` = bit real (0/1). Compara con el coseno entre `p` y `c`; elige con el arnés. Ambas variantes pueden entrar como features.

## Regla crítica
El ranking por Tanimoto es sensible a los errores del fingerprint. **Nunca lo uses como criterio único:** se combina siempre con la señal espectral directa del Pilar A y el error de masa dentro del ensamble (skill 11).

## Entrenamiento / fine-tuning de MIST
- Respeta los splits de la skill 04: MIST nunca puede ver las moléculas de validación del fold (genera predicciones out-of-fold para el ensamble).
- Presupuesta el tiempo: decide con medidas si afinas desde pesos preentrenados o entrenas desde cero; documenta el compromiso.
- Guarda el checkpoint con su configuración para empaquetarlo como dataset (skill 13).

## Salidas para el ensamble
Por candidato: `b_tanimoto_soft`, `b_cosine_fp`, `b_rank_in_formula`, `b_n_candidates_formula`, `b_formula_conf`, `b_formula_ppm`, `b_dbe`, `b_cosmic` (si hay SIRIUS), `b_sources_count`.

## Verificación
MRR@25 en Val-Clase2 por semilla; desglosa por tamaño del conjunto de candidatos de la fórmula y por confianza de fórmula para ver dónde falla. Reporta también el *recall@25* del universo (¿está la estructura verdadera entre los candidatos?): si el recall del universo es bajo, el cuello de botella son las bases de datos, no el modelo.
