---
name: casmi-05-candidate-universe
description: Construcción y consulta del universo de candidatos moleculares por fórmula para CASMI 2026 — PubChem, COCONUT, LOTUS (productos naturales) y HMDB — con deduplicación por InChIKey14, fingerprints precalculados, verificación de licencia comercial y empaquetado offline. Úsala siempre que se necesiten estructuras candidatas para una fórmula, se amplíen bases de datos, se hable de PubChem/COCONUT/LOTUS/HMDB, o se prepare el índice fórmula→SMILES para los pilares B y C.
---

# Universo de candidatos

## Objetivo
Dada una fórmula molecular exacta, devolver rápidamente todas las estructuras conocidas con esa composición. Alimenta el Pilar B (matching por Tanimoto) y sirve de filtro de plausibilidad para el Pilar C. El dataset de Enveda proviene de plantas y microbios, así que los productos naturales (LOTUS, COCONUT) son críticos: PubChem solo cubre mal ese dominio.

## Fuentes
| Fuente | Aporte | Nota |
|---|---|---|
| PubChem | Cobertura general | Muy grande: filtra por rango de masa (~150–1,200 Da) y elementos permitidos |
| COCONUT | Productos naturales | — |
| LOTUS | Productos naturales con taxonomía planta/organismo | Parientes cercanos de moléculas "fantasma" |
| HMDB | Metaboloma humano | **Verifica la licencia** antes de incluirla |

**Licencias (obligatorio):** la competencia solo permite datos externos públicos con licencia comercial válida. Antes de incluir cada fuente, localiza su licencia y regístrala en `candidate_sources.md` (fuente, versión, fecha de descarga, licencia, URL). Si una licencia restringe el uso comercial (se sospecha de HMDB; confírmalo en su sitio), **pregunta al usuario** y revisa las reglas de la competencia antes de incluirla. No asumas.

## Pipeline de construcción
1. Descarga las fuentes **localmente** (en el entorno de Kaggle no habrá internet en la evaluación).
2. Estandariza (desalinizar, quitar fragmentos pequeños, neutralizar; `rdMolStandardize`/`molvs`), filtra por elementos y masa, y calcula **InChIKey14** con la función de la skill 01.
3. **Deduplica por InChIKey14**, conservando una lista de fuentes por estructura (`sources`: bitmask) — el número de bases que contienen una estructura es una feature útil.
4. Calcula fórmula en notación Hill y masa monoisotópica exacta.
5. Guarda en **parquet particionado por fórmula** (o SQLite indexado por `formula`). Columnas: `inchikey14`, `smiles`, `formula`, `mono_mass`, `sources`, `fp` (opcional, ver abajo).
6. Fingerprints: calcula el fingerprint **con la misma definición que usa MIST** (skill 08); si no coinciden, el Tanimoto no tiene sentido. Valora precalcularlos solo para formulas candidatas del test para ahorrar disco.
7. Versiona el resultado y empaquétalo como dataset de Kaggle (skill 13).

## Consulta
`get_candidates(formula, k_max=None)` → DataFrame. Si una fórmula devuelve 0 candidatos, es una señal fuerte de Clase 3 (o de fórmula errónea): regístralo como feature `n_candidates_formula`. Si devuelve miles, el ranking depende por completo del fingerprint; considera un prefiltrado barato.

## Reglas para la validación
- En Val-Clase3 (skill 04) la estructura verdadera debe estar **ausente** del universo; el generador del arnés debe hacer esa exclusión por InChIKey14.
- Exige que no se filtre información del test: nunca incluyas en el universo estructuras derivadas del propio test.

