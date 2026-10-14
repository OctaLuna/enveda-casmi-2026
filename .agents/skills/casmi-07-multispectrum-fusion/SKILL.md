---
name: casmi-07-multispectrum-fusion
description: Fusión multi-espectro por molecule_id para CASMI 2026 — agregación ponderada de embeddings DreaMS de todos los spectrum_id de una molécula, consistencia entre energías de colisión y entre aductos, y espectro de consenso. Úsala siempre que una molécula tenga varios espectros, se quiera reducir ruido instrumental, se agreguen embeddings o picos por molécula, o se busque una señal adicional para el filtrado de fórmula.
---

# Fusión multi-espectro

## Idea
Una molécula del test suele traer varios `spectrum_id` (distintos aductos y energías de colisión). Tratarlos como consultas independientes desperdicia información y aumenta la varianza. Agrégalos **por `molecule_id`** antes del retrieval final del Pilar A y úsalos como evidencia conjunta para fórmula y fingerprint.

## 1. Fusión de embeddings (Pilar A)
- Promedia los embeddings DreaMS de los espectros de la molécula con **pesos de calidad**: nº de picos tras limpieza (skill 02), intensidad total, ausencia de flags de calidad. Renormaliza L2.
- Alternativa más robusta: búsqueda por espectro individual y **fusión de rankings** (suma de scores o rank fusion). Compara ambas opciones en el arnés (skill 04); no asumas cuál gana.
- Reporta `n_spectra` y la dispersión de los embeddings (baja dispersión = consistencia alta) como features.

## 2. Consistencia entre energías de colisión
Los picos que persisten a través de varias energías de colisión suelen ser fragmentos estructuralmente robustos. Construye un **espectro de consenso**: fusiona los picos (tolerancia de m/z), cuenta en cuántos espectros aparece cada pico y conserva/pondera los persistentes. Úsalo como señal adicional en el filtrado de fórmula del Pilar B (cada pico persistente debe ser una subfórmula de la fórmula del precursor; skill 03) y como entrada alternativa al predictor de fingerprint (skill 08).

## 3. Consistencia entre aductos
Convierte cada espectro a masa neutra (skill 03). Si todas las masas neutras coinciden dentro de la tolerancia, sube la confianza de la fórmula; si no, marca la molécula para revisar aductos mal etiquetados. Esa discrepancia es una feature (`adduct_mass_spread_ppm`).

## Reglas
- La fusión se aplica a train (para entrenar con la misma distribución) y a test; usa la misma función en ambos.
- Cuida el desbalance: moléculas con decenas de espectros no deben dominar el entrenamiento; limita o submuestrea.
- Verifica que la fusión mejora el MRR@25 por clase frente a no fusionar; si no mejora en una clase, desactívala allí.

