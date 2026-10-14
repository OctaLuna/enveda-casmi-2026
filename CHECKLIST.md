# CHECKLIST.md — Checklist Maestro de Ejecución CASMI 2026

> Basado en la Sección 11 del Masterplan Técnico de Enveda CASMI 2026.
> Este checklist es auditado automáticamente por el hook `H52` (`checklist-sync`).

---

## Fase 0: Infraestructura, Gobernanza y Hooks
- [x] Crear constantes de proyecto centralizadas en `.agents/project.json`.
- [x] Configurar arnés de memoria y gobernanza universal en `AGENTS.md` y `CLAUDE.md`.
- [x] Implementar despachador de hooks multi-agente `.agents/bin/agent-hook` y `registry.json`.
- [x] Implementar hooks de seguridad H10–H14 (secretos, protección de crudos, archivos grandes, comandos peligrosos, modo offline).
- [x] Implementar hooks de dominio CASMI H20–H30 (RDKit pin, canonicalización, splits, MRR@25, submission, aductos, presupuesto).
- [x] Implementar hooks de calidad H40–H43 y trazabilidad H50–H52.
- [x] Activar hooks de Git G01–G06 vía `core.hooksPath .agents/git-hooks`.
- [x] Crear suite de pruebas de aceptación de hooks en `.agents/bin/selftest.py`.

---

## Fase 1: Fundamentos de Quimioinformática y Datos
- [ ] Implementar canonicalización tautomérica estricta con RDKit `2026.03.3` (`rdMolStandardize.TautomerEnumerator`) e InChIKey14.
- [ ] Implementar y validar cálculo de métrica oficial MRR@25 (solo primera coincidencia, top-25).
- [ ] Implementar conversor de `precursor_mz` a masa neutra según aducto (`[M+H]+`, `[M-H]-`, etc.).
- [ ] Implementar deisotopado explícito colapsando isotopos (+1, +2 Da).
- [ ] Implementar cargador eficiente de `train.parquet` y `test.parquet`.
- [ ] Crear particiones anti-leakage por `molecule_id` con clustering MCES / Murcko Scaffolds para 3 semillas (`Val-Clase1`, `Val-Clase2`, `Val-Clase3`).

---

## Fase 2: Universo de Candidatos y Pilar A (Retrieval)
- [ ] Descargar y preprocesar bases de datos moleculares públicas (PubChem, COCONUT, LOTUS, HMDB) con deduplicación por InChIKey14.
- [ ] Validar licencias comerciales de bases de datos externas en `docs/DATA_SOURCES.md`.
- [ ] Extraer embeddings DreaMS de espectros MS/MS.
- [ ] Construir y ajustar índice FAISS IVF-PQ sobre ~2M vectores espectrales.
- [ ] Implementar similitud por entropía espectral y coseno con `matchms`.

---

## Fase 3: Pilar B (Fingerprints) y Fusión Multi-Espectro
- [ ] Entrenar/afinar predictor neuronal MIST desde espectros MS/MS.
- [ ] Filtrar candidatos por fórmula molecular / masa neutra exacta.
- [ ] Calcular ranking por similitud Tanimoto contra universo de candidatos.
- [ ] Implementar fusión multi-espectro agregando múltiples energías de colisión y aductos por `molecule_id`.

---

## Fase 4: Pilar C (De Novo) y Cycle-Consistency
- [ ] Implementar generación molecular de novo con DiffMS restringida por fórmula molecular.
- [ ] Integrar modelo forward (CFM-ID / ICEBERG) para re-simular espectros de candidatos de novo.
- [ ] Reordenar candidatos generados por cycle-consistency spectral similarity.

---

## Fase 5: Ensamble, Presupuesto y Kaggle Packaging
- [ ] Entrenar re-ranker LightGBM / XGBoost optimizado para MRR@25 con features de los 3 pilares.
- [ ] Calibrar cascada de inferencia en `configs/budget.yaml` asegurando ejecución en $< 450$ min (margen 20% sobre 9h).
- [ ] Catalogar todos los pesos en `kaggle/manifest.yaml` con slug, versión y SHA-256.
- [ ] Probar generación y validación de `submission.csv` en entorno offline.

