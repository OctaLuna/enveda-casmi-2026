# Tareas Atómicas SDD: 002_formula_and_candidates
## Desglose de Tareas (<30 min) para Dev 1 (Octavio Luna)

> **ID de Tareas**: `TASKS-002`  
> **Feature**: Estimador de Fórmulas y Universo de Candidatos (Pilar B)  
> **Regla de Cierre**: Prohibido marcar `[x]` sin la ejecución previa y exitosa de la prueba unitaria correspondiente (`pytest tests/... -v`).

---

## Bloque 1: Restricciones Químicas de Senior y DBE (Días 1-2)

- [x] `[DEV1-T2.1]` [RF: REQ-EVT-02, REQ-EVT-03] Implementar `src/data/chemical_filters.py` con Teorema de Valencia de Senior (Reglas 1, 2 y 3), cálculo de DBE y ratios elementales.  
  *Estimación*: 25 min | *Dependencias*: Ninguna | *DoD*: `tests/test_chemical_filters.py` passing con moléculas reales e imposibles.

---

## Bloque 2: Estimador de Fórmula Molecular Exacta (Días 3-5)

- [x] `[DEV1-T2.2]` [RF: REQ-UBI-01, REQ-UBI-02, REQ-UBI-03, REQ-EVT-01] Implementar `src/data/formula_estimator.py` para generar fórmulas en notación Hill dentro de tolerancia ppm, calculando DBE, error y confianza.  
  *Estimación*: 30 min | *Dependencias*: T2.1 | *DoD*: `tests/test_formula_estimator.py` passing para productos naturales conocidos.

---

## Bloque 3: Base e Indexador de Candidatos por Fórmula (Días 6-8)

- [x] `[DEV1-T2.3]` [RF: REQ-EVT-04, REQ-EVT-05, REQ-STA-01] Implementar `src/data/candidate_db.py` para indexación y consulta $O(1)$ por fórmula molecular con deduplicación por InChIKey14.  
  *Estimación*: 30 min | *Dependencias*: T2.2 | *DoD*: `tests/test_candidate_db.py` passing.

- [x] `[DEV1-T2.4]` [Gobernanza H29] Actualizar `docs/DATA_SOURCES.md` con la auditoría de licencias comerciales de PubChem, COCONUT, LOTUS y HMDB.  
  *Estimación*: 15 min | *Dependencias*: Ninguna | *DoD*: Verificación con `.agents/bin/selftest.py` passing.

---

## Bloque 4: Suite de Validación de Productos Naturales Complejos (Días 9-10)

- [x] `[DEV1-T2.5]` [DoD Sprint 2] Implementar y ejecutar suite integral de productos naturales complejos (alcaloides, flavonoides, glicósidos) y verificar cobertura $\ge 85\%$.  
  *Estimación*: 20 min | *Dependencias*: T2.1, T2.2, T2.3 | *DoD*: Cobertura $\ge 85\%$ en `src/data/` y 0 fallos en linters.
