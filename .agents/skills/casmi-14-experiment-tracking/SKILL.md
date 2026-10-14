---
name: casmi-14-experiment-tracking
description: Registro y seguimiento de experimentos y envíos para CASMI 2026 — MRR@25 público del leaderboard vs. MRR@25 local por clase y semilla, configuración, tiempos y detección de sobreajuste al leaderboard o de proporción de clases distinta a la asumida. Úsala siempre que se haga o planee una submission, se compare un resultado del leaderboard con la validación local, se decida qué notebook seleccionar, o se pregunte "¿esto mejoró de verdad?".
---

# Seguimiento de experimentos y envíos

## Objetivo
El leaderboard público (~400 moléculas) tiene alta varianza. Registrar **cada envío** junto con el desempeño local por clase permite (a) detectar sobreajuste al público, (b) estimar la proporción real de las clases en el test y (c) decidir qué notebook seleccionar al cierre.

## Registro obligatorio por envío
Mantén un archivo único (`experiments/log.csv` o similar) con una fila por envío:

| Campo | Contenido |
|---|---|
| `date`, `notebook_version`, `git_commit` | Identificación reproducible |
| `config_hash` | Hash de la configuración (umbrales, K, N de muestras, features activas) |
| `public_mrr25` | Score del leaderboard público |
| `local_mrr25_c1/c2/c3` | MRR@25 medio en Val-Clase1/2/3 |
| `local_mrr25_c1/c2/c3_std` | Desviación entre semillas (≥ 3 semillas) |
| `runtime_min`, `runtime_by_stage` | Tiempos (skill 12) |
| `notes` | Qué cambió respecto al envío anterior |

## Análisis
1. **Correlación público vs. local:** si el MRR público sube pero el local por clase no (o al revés), sospecha ruido del público o desajuste de validación (revisa la skill 01: ¿versión de RDKit? ¿canonicalización?).
2. **Proporción real de clases:** con ≥ 3–4 envíos distintos, ajusta `public ≈ w1·c1 + w2·c2 + w3·c3` (pesos no negativos que suman 1) por mínimos cuadrados no negativos. Con pocos puntos el ajuste es inestable: preséntalo como estimación con incertidumbre, no como hecho. Úsalo para priorizar la clase donde más se pueda ganar.
3. **Reglas anti-overfitting:** no afines hiperparámetros solo contra el leaderboard público; una mejora local que se confirma en ≥ 3 semillas y en las clases relevantes vale más que +0.005 en el público.
4. **Selección final:** elige el notebook por **MRR local robusto (por clase y semilla) + público**, y comprueba que corre dentro del tiempo con la mayor holgura; ante empates, prefiere el más simple y robusto.

## Cuotas
Consulta en Kaggle el número máximo de envíos por día y planifícalos; guarda envíos para las últimas dos semanas, cuando más se necesitan.
