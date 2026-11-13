# DEV2-T4.4: comparación de estrategias en Val-Clase1

**Estado:** benchmark completo con la regla final de ranking
**Ejecución:** Kaggle, kernel `leonardoibarralpez/casmi-26-valclase1-baseline-benchmark`, versión 19 ([kernel](https://www.kaggle.com/code/leonardoibarralpez/casmi-26-valclase1-baseline-benchmark))
**Dataset de código:** `leonardoibarralpez/casmi-src`, actualizado inmediatamente antes de ejecutar v19 con el matcher corregido
**Split:** `split_seed_42.json`, semilla 42
**Cobertura:** las 3,370 consultas Val-Clase1 del manifiesto; evaluación completa, sin muestreo ni ajuste de pesos sobre este split.

## Qué se compara

Se compara el matcher baseline con dos estrategias de ranking sobre el mismo índice de train y las mismas consultas:

1. `cosine`: similitud coseno de fragmentos, pesos efectivos (1.00, 0.00).
2. `weighted_fusion`: combinación fija de coseno y entropía espectral, pesos (0.50, 0.50).

El ranking ordena por score espectral descendente. Si dos candidatos empatan en score, prioriza la menor diferencia absoluta de `precursor_mz`; si también empatan en masa, usa SMILES ascendente. Los pesos se mantuvieron fijos y no se optimizaron con Val-Clase1.

## Resultados finales de Kaggle v19

| Estrategia | Pesos (coseno, entropía) | MRR@25 | Latencia media de predicción (ms/consulta) | Consultas |
|---|---:|---:|---:|---:|
| `cosine` | 1.00, 0.00 | 0.8230 | 2,390.271 | 3,370 |
| `weighted_fusion` | 0.50, 0.50 | 0.8736 | 3,433.492 | 3,370 |

La fusión supera al coseno por **0.0506 MRR@25** y añade **1,043.221 ms/consulta** de latencia media (43.6% más). Esto solo compara las dos configuraciones indicadas; no es una búsqueda de hiperparámetros.

## Reproducibilidad y validez

- El benchmark cargó 2,539,608 filas del train y seleccionó 261,378 espectros de 22,379 moléculas para el índice a partir del manifiesto de semilla 42.
- La verdad de terreno y los candidatos se compararon por el `molecule_id` oficial de train (InChIKey14). Cada etiqueta SMILES recuperada se mapeó a su ID oficial y se deduplicó por ID antes del top 25. Esto conserva la identidad de la métrica sin depender de RDKit, no disponible en la imagen offline de Kaggle.
- El evaluador comprueba que estén todas las consultas del manifiesto, que cada consulta pertenezca a train, que haya como máximo una consulta por molécula y que las etiquetas recuperadas tengan un mapeo único a ID oficial.
- El log de Kaggle registra **19,755.2 s (5 h 29 min 15 s)** hasta la conversión final de resultados. La ejecución queda dentro del límite de 9 horas, con aproximadamente **3 h 30 min 45 s** de margen. La latencia tabulada mide solo predicción, no carga ni construcción del índice.
- Como referencia para la meta de 15 minutos mencionada en la revisión, una proyección lineal a 1,500 espectros de test da aproximadamente **59.8 min** con coseno y **85.8 min** con fusión, antes de contar carga e indexación. Es una extrapolación, no una medición de test; indica que el baseline todavía requiere una optimización de retrieval para cumplir esa meta.
- El artefacto final es `val_clase1_full_seed42.md` del output de la versión 19. El log `casmi-26-valclase1-baseline-benchmark.log` conserva los tiempos y la salida de ejecución. Los dos artefactos crudos permanecen en el directorio local ignorado `kaggle_datasets/` y no se versionan.
- La versión 18, con ranking sin desempate por precursor, reportó MRR@25 de 0.8218 para coseno y 0.8730 para fusión. Esos resultados quedan supersedidos por esta ejecución, que usa la regla final.

## Verificación local

- `pytest tests/test_baseline_pipeline.py tests/test_models.py tests/test_evaluation.py tests/test_spectral_similarity.py -q`: **30 passed**.
- Ruff pasó en los ocho archivos de código y pruebas relacionados con esta revisión.
- Black confirmó los ocho archivos sin cambios requeridos.
- `git diff --check` pasó.

**Conclusión:** DEV2-T4.4 cumple su DoD con resultados de la implementación final. La fusión fija de 0.50/0.50 alcanza el mejor MRR de las dos estrategias evaluadas en este split, con mayor latencia. DEV2-T4.4 cumple su DoD de comparación; la proyección de runtime queda como pendiente de optimización antes de adoptar este baseline para la inferencia final.
