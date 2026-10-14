---
name: casmi-12-compute-cascade
description: Presupuesto de cómputo y arquitectura en cascada (Clase 1 → Clase 2 → Clase 3) dentro del límite de 9 horas de Kaggle para CASMI 2026 — gating por confianza, minutos por molécula, margen de seguridad, checkpoints y submission parcial de respaldo. Úsala siempre que se hable de tiempo de ejecución, timeouts, optimización de velocidad, orden de ejecución de los pilares, umbrales de confianza o de si el notebook cabe en 9 horas.
---

# Cascada y presupuesto de cómputo

## Restricción
Máximo **9 h** (CPU o GPU) por ejecución, sin internet. Con ~400 moléculas, la cascada es **obligatoria**: Clase 1 (rápido, retrieval) → Clase 2 (medio, fingerprint + matching) → Clase 3 (costoso, generación + verificación forward). El Pilar C solo se aplica a las moléculas que A y B no resuelven con alta confianza.

## Procedimiento
1. **Mide, no estimes.** Cronometra cada etapa en el hardware real de Kaggle con una submuestra: embeddings DreaMS, FAISS, MIST, consulta de candidatos, DiffMS (s/muestra), forward CFM-ID/ICEBERG (s/candidato), ranker.
2. **Tabla de presupuesto** (rellénala con números medidos):

| Etapa | Nº moléculas | min/molécula | Total (min) |
|---|---|---|---|
| Carga + preprocesado + embeddings | todas | _medir_ | _medir_ |
| Pilar A (retrieval + entropía) | todas | _medir_ | _medir_ |
| Pilar B (fórmula + MIST + matching) | todas | _medir_ | _medir_ |
| Pilar C (DiffMS) | solo no resueltas | _medir_ | _medir_ |
| Cycle-consistency | solo no resueltas, top-K | _medir_ | _medir_ |
| Ensamble + escritura | todas | _medir_ | _medir_ |

3. **Margen de seguridad:** reserva ~15–20 % del tiempo total para la variabilidad del hardware de Kaggle. Ese margen es parte del presupuesto, no un extra.
4. **Gating por confianza:** define umbrales (p. ej. score espectral del Pilar A, confianza del ensamble parcial) calibrados con el arnés (skill 04) para decidir qué moléculas "pasan" al siguiente nivel. Elige los umbrales maximizando MRR@25 **bajo la restricción de tiempo**, no solo el MRR.
5. **Reparto adaptativo:** si el tiempo restante cae por debajo de un umbral, el pipeline reduce N de muestras de DiffMS y K de verificación forward en vez de fallar.

## Robustez (obligatorio)
- **Escribe `submission.csv` temprano** con la salida del Pilar A/B, y **sobrescríbelo** al completar cada nivel. Si el notebook se corta, queda una entrega válida.
- **Reloj de guardia:** una función `time_left()` consultada antes de cada molécula/lote; al llegar al margen, cierra y escribe lo que haya.
- **Checkpoints** por lote en disco (parquet) para reanudar sin repetir trabajo.
- Paraleliza con cuidado (memoria): el límite de RAM de Kaggle puede ser el cuello de botella antes que el CPU.
- Registra en un log el tiempo por etapa y por molécula para el seguimiento (skill 14).

## Verificación
Ejecuta el notebook completo, de extremo a extremo, **con internet desactivado**, y comprueba que termina en ≲ 80 % del límite (≈ 7.2 h) antes de dar el pipeline por válido.

