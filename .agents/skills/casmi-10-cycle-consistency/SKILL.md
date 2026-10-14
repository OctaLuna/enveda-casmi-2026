---
name: casmi-10-cycle-consistency
description: Verificación por cycle-consistency para CASMI 2026 — re-simular el espectro teórico de cada candidato de novo con un modelo forward (CFM-ID o ICEBERG) y compararlo con el espectro observado para reordenar candidatos de Clase 3. Úsala siempre que se prediga un espectro desde un SMILES, se use CFM-ID/ICEBERG, se calcule una puntuación de consistencia, o se necesite reordenar candidatos generados; es la mayor ventaja diferencial del pipeline.
---

# Cycle-consistency (verificación forward)

## Idea
Para cada candidato generado, simula su espectro teórico con un modelo *forward* y compáralo contra el espectro real. Un candidato correcto debería reproducir el espectro observado. Esta señal de consistencia reordena los candidatos de novo y es la técnica que distingue a los mejores resultados en la categoría de novo.

## Modelos forward
- **ICEBERG** (repositorio `coleygroup/ms-pred`) y **CFM-ID**. Verifica en sus README: instalación offline, formato de entrada (SMILES, aducto, energía de colisión), tiempo por molécula, uso de GPU y licencia. CFM-ID puede requerir compilación/contenedor; confirma que puede empaquetarse y ejecutarse en un notebook de Kaggle **sin internet** (skill 13) antes de comprometerte con él.
- Decide con medidas cuál usar (o ambos) comparando mejora de MRR@25 en Val-Clase3 por segundo de cómputo.

## Costo y estrategia
La verificación forward es **la parte más cara** del pipeline. Por eso:
1. Se aplica **solo a las moléculas no resueltas con alta confianza** por los pilares A y B (cascada, skill 12).
2. Solo sobre el **top-K** de candidatos preordenados por el ensamble previo (p. ej. K = 10–50; calibra con el arnés).
3. **Cachea** por (SMILES, aducto, energía) y paraleliza; descarta duplicados por InChIKey14 antes de simular.
4. Mide segundos/candidato en el hardware de Kaggle y reporta el presupuesto a la skill 12.

## Comparación espectro simulado vs. observado
- Simula con el **mismo aducto y energía(s) de colisión** que cada espectro observado; si hay varios espectros por molécula (skill 07), compara con cada uno y agrega (media y máximo).
- Similitud: coseno con tolerancia de m/z y/o *spectral entropy similarity* (skill 06). Usa ambas como features.
- Preprocesa el espectro observado con la skill 02 antes de comparar.

## Salidas para el ensamble
Por candidato: `cc_cosine_mean`, `cc_cosine_max`, `cc_entropy_mean`, `cc_n_peaks_explained`, `cc_available` (0/1 si no se pudo simular por límite de tiempo). El ensamble debe tolerar que esta feature falte (valor nulo explícito, no 0).

## Verificación
Mide la ganancia incremental de MRR@25 en Val-Clase3 al añadir `cc_*` y reporta cuánto cuesta en minutos; esa relación decide cuántas moléculas y cuántos candidatos verificar dentro del presupuesto de 9 h.

