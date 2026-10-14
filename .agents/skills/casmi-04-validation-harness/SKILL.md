---
name: casmi-04-validation-harness
description: Arnés de validación local anti-overfitting para Enveda CASMI 2026 — split por molecule_id con agrupamiento estructural (MCES, scaffold de Murcko o clustering ECFP4/Tanimoto), los tres subsets Val-Clase1/2/3, múltiples semillas y reporte de MRR@25 por clase. Úsala siempre que se cree un split train/validación, se evalúe un modelo, se compare una mejora, se hable de leakage, overfitting al leaderboard, varianza o "¿esto realmente mejoró?". Ninguna mejora cuenta hasta medirla aquí.
---

# Arnés de validación de 3 clases

## Principio
Un split aleatorio sobreestima el rendimiento: deja "primos estructurales" en train que hacen trivial la Clase 3. El arnés debe **simular las tres condiciones del test oculto** y reportarlas por separado.

## Reglas de split
1. **Por `molecule_id`, nunca por `spectrum_id`** (evita que espectros de la misma molécula caigan en lados distintos).
2. **Agrupamiento estructural.** Preferido: distancia **MCES** (máximo subgrafo común de aristas); busca una implementación de MCES (p. ej. el paquete `myopic-mces`) y confirma que esté disponible y sea utilizable offline. Alternativas, de mejor a peor: clustering de fingerprints ECFP4 con Tanimoto (Butina o agrupamiento jerárquico con umbral) → scaffold de Murcko. MCES exacto es costoso en 275 k moléculas: usa un prefiltrado por Tanimoto y calcula MCES solo entre vecinos cercanos, o acepta ECFP4 si el tiempo no alcanza.
3. Asigna **clusters completos** a validación con `GroupKFold`/`GroupShuffleSplit` (los grupos son los clusters estructurales).

## Los tres subsets
| Subset | Espectro en índice de búsqueda | SMILES en base de candidatos | Simula |
|---|---|---|---|
| Val-Clase1 | Sí | Sí | Búsqueda directa |
| Val-Clase2 | No | Sí | Estructura conocida, sin espectro |
| Val-Clase3 | No | No | Molécula fantasma (de novo) |

**Construcción práctica** (resuelve la tensión con la regla "por molecule_id"):
- **Val-Clase1:** moléculas con ≥ 2 espectros; reserva uno como *query* (idealmente de otro aducto o energía de colisión) y deja el resto en el índice. Los espectros *query* **no** pueden usarse para entrenar ni afinar nada.
- **Val-Clase2:** todos los espectros de la molécula salen del índice y del train; el SMILES permanece en el universo de candidatos.
- **Val-Clase3:** igual que Clase 2, pero **además** se eliminan del universo de candidatos su InChIKey14 **y** se retiran de train los vecinos estructurales cercanos (el cluster completo está fuera de train).

## Reglas de higiene
- Todo modelo que genere features para el ensamble (DreaMS afinado, MIST, DiffMS) debe entrenarse **sin** las moléculas de validación del fold correspondiente; las features para el ensamble se generan **out-of-fold** (ver skill 11).
- El universo de candidatos de cada subset debe construirse con las mismas reglas que en producción (misma fórmula, mismas fuentes), salvo la exclusión intencional de la Clase 3.
- **≥ 3 semillas** de split distintas; reporta media ± desviación por clase. El test real tiene ~400 moléculas: alta varianza muestral.
- Usa la función de métrica de la skill 01, nunca una reimplementación.

## Salida estándar
Tabla por (semilla, clase): `n_moléculas`, `MRR@25`, `top1`, `top5`, `top25_recall`. Guarda splits y semillas en disco (parquet/JSON versionado) para que cualquier experimento sea reproducible.

## Uso en decisiones
El leaderboard será aproximadamente un promedio ponderado por la proporción real (desconocida) de cada clase. Usa los tres números para decidir **dónde invertir**: si Clase 3 es la más débil y la más probable según el leaderboard público, prioriza los pilares C y 10; si la Clase 1 domina, prioriza el pilar A. Estima la proporción real contrastando el MRR público con los MRR por clase (skill 14).

