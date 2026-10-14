---
name: casmi-01-metric-canonicalization
description: Implementa y verifica la métrica MRR@25 y la canonicalización de SMILES (tautómeros con RDKit rdMolStandardize, primer bloque del InChIKey = InChIKey14) del desafío Enveda CASMI 2026. Úsala siempre que se calcule un score local, se compare un SMILES predicho contra el real, se deduplique un top-25, se configure la versión de RDKit, o el MRR local no coincida con el leaderboard. Imprescindible antes de cualquier validación.
---

# Métrica y canonicalización

## Por qué importa
El evaluador canonicaliza predicción y verdad con RDKit (tautómeros) y compara solo el **InChIKey14** (primer bloque del InChIKey). Si el pipeline local difiere, el MRR@25 local deja de correlacionar con el leaderboard y todas las decisiones de modelado quedan sesgadas. Esta es la base de todo el proyecto.

## Reglas
1. **Versión de RDKit fija.** El masterplan indica RDKit `2026.03.3` (pip lo normaliza como `2026.3.3`). Comprueba `rdkit.__version__` en local **y** en el entorno de Kaggle; si difieren, avisa al usuario. Confirma además contra la página *Evaluation* de la competencia si el procedimiento exacto cambió.
2. **Misma canonicalización:** `rdMolStandardize.TautomerEnumerator().Canonicalize(mol)` → InChIKey → primer bloque (14 caracteres antes del primer `-`). No se penalizan estereocentros ni forma tautomérica.
3. **MRR@25:** rango de la **primera** coincidencia correcta; 1/rank; 0 si no está en el top-25. Promedio sobre moléculas.
4. **Deduplica por InChIKey14 antes de truncar a 25.** Dos SMILES que canonicalizan al mismo InChIKey14 ocupan dos posiciones pero solo una puede acertar; los duplicados desperdician espacio. Deduplica manteniendo el orden y luego corta a 25.
5. **SMILES inválidos:** descártalos antes de enviar; un SMILES que no parsea es un hueco perdido.
6. **Prueba de regresión:** guarda un pequeño conjunto de pares (SMILES, InChIKey14 esperado) y verifícalo en cada ejecución local; verifica también que dos tautómeros conocidos den el mismo InChIKey14.

## Implementación
Usa `scripts/canon.py` (funciones `inchikey14`, `dedupe_topk`, `mrr_at_k`, `selftest`). Impórtalo desde el resto del proyecto en lugar de reescribir la lógica; así hay una única fuente de verdad.

```python
from canon import inchikey14, dedupe_topk, mrr_at_k
ranked = dedupe_topk(raw_candidates, k=25)
score = mrr_at_k(preds={"mol_1": ranked}, truth={"mol_1": true_smiles}, k=25)
```

## Rendimiento
Canonicalizar tautómeros es lento. Cachea `smiles → inchikey14` (dict o `functools.lru_cache`) y paraleliza con `multiprocessing` al procesar millones de candidatos. Precalcula el InChIKey14 de las bases de candidatos una sola vez.
