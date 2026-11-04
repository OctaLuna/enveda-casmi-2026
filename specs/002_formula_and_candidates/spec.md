# Especificación SDD: 002_formula_and_candidates
## Estimación de Fórmula Molecular, Restricciones Químicas de Senior y Base de Candidatos

> **ID de Especificación**: `SPEC-002`  
> **Estado**: Aprobado para Ejecución  
> **Área**: Química Computacional & Universo de Candidatos (Pilar B)  
> **Lead Asignado**: Octavio Luna (Dev 1 — Data & Validation Lead)  

---

## 1. Propósito y Alcance

### 1.1 Dentro de Alcance (In-Scope)
Esta especificación define los requisitos formales para los módulos químicos de soporte del Pilar B:
- Estimación precisa de fórmulas moleculares elementales (CHNOPS + halógenos opcionales F, Cl, Br, I) a partir de la masa neutra exacta $M$ corregida por aducto.
- Filtrado estricto por restricciones de valencia atómica de Senior (reglas 1, 2 y 3) y grado de insaturación DBE (*Double Bond Equivalents* $\ge 0$, entero).
- Filtrado por ratios elementales heurísticos para metabolitos secundarios y productos naturales ($0.1 \le H/C \le 3.0$, $O/C \le 1.2$, $N/C \le 0.6$, $P/C \le 0.3$, $S/C \le 0.3$).
- Cálculo de error de masa en partes por millón ($\Delta\text{ppm}$) y emisión de un score de confianza de fórmula normalizado.
- Indexación y consulta en memoria/offline $O(1)$ de estructuras candidatas particionadas por fórmula molecular exacta en formato canónico de Hill.
- Deduplicación de candidatos por el primer bloque del InChIKey (`InChIKey14`) para maximizar la diversidad del ranking y no saturar el top-25.
- Auditoría formal de licencias comerciales de bases de datos externas en `docs/DATA_SOURCES.md` bajo el Hook `H29`.

### 1.2 Fuera de Alcance (Out-of-Scope)
- **Predicción de Fingerprints Neuronales con MIST**: Asignado a Joan Riveros (Dev 3) en `src/models/fingerprints/mist_predictor.py`.
- **Ranking de Tanimoto con Fingerprints**: Asignado a Joan Riveros (Dev 3) en `src/models/fingerprints/tanimoto_ranker.py`.
- **Búsqueda Vectorial de Embeddings DreaMS**: Asignado a Leonardo Ibarra (Dev 2) en `src/models/retrieval/`.

---

## 2. Requisitos Funcionales en Sintaxis EARS

### 2.1 Requisitos Ubicuos (Ubiquitous Requirements)
* **[REQ-UBI-01]**: El sistema debe representar todas las fórmulas moleculares en la notación canónica del sistema Hill (primero Carbono, segundo Hidrógeno, y el resto en orden alfabético).
* **[REQ-UBI-02]**: El sistema debe utilizar masas atómicas monoisotópicas de alta resolución de la IUPAC para el cómputo de masa neutra teórica y error en ppm.
* **[REQ-UBI-03]**: El sistema debe asegurar que el error de masa relativo se calcule estrictamente como:
  $$\Delta\text{ppm} = \frac{M_{\text{teorica}} - M_{\text{observada}}}{M_{\text{observada}}} \times 10^6$$

### 2.2 Requisitos Basados en Eventos (Event-Driven Requirements)
* **[REQ-EVT-01]**: CUANDO el estimador de fórmula reciba una masa neutra $M$ y una tolerancia en ppm (default $\pm 5\text{--}10\text{ ppm}$), el sistema debe generar todas las combinaciones elementales posibles dentro de los límites CHNOPS.
* **[REQ-EVT-02]**: CUANDO se evalúe una fórmula candidata, el sistema debe descartarla SI no satisface el Teorema de Valencia de Senior (suma de valencias par $\ge 2 \cdot \max(v)$ y $\ge 2 \cdot (n - 1)$).
* **[REQ-EVT-03]**: CUANDO se evalúe una fórmula candidata neutra, el sistema debe verificar que su grado de insaturación DBE sea un número entero no negativo ($DBE \ge 0$ y $2 \cdot DBE \in 2\mathbb{Z}$).
* **[REQ-EVT-04]**: CUANDO se consulte la base de candidatos con una fórmula molecular, el indexador debe devolver todos los candidatos asociados en tiempo promedio $O(1)$.
* **[REQ-EVT-05]**: CUANDO se indexen múltiples registros moleculares que compartan el mismo `InChIKey14`, el sistema debe consolidarlos en una única entrada conservando el listado de fuentes de procedencia.

### 2.3 Requisitos Basados en Estado (State-Driven Requirements)
* **[REQ-STA-01]**: MIENTRAS el indexador de candidatos opere en el entorno de evaluación offline de Kaggle, el sistema debe responder consultas sin recurrir a conexiones remotas a internet.

### 2.4 Requisitos de Comportamiento No Deseado (Unwanted Behavior Requirements)
* **[REQ-ERR-01]**: SI la masa neutra observada $M \le 0$ o la tolerancia en ppm $\le 0$, ENTONCES el estimador debe rechazar la consulta y devolver una lista vacía de candidatos con advertencia estructurada.
* **[REQ-ERR-02]**: SI una fórmula elemental viola las reglas de valencia atómica de Senior, ENTONCES el sistema debe excluirla de la lista de candidatos con flag `senior_valid = False`.

---

## 3. Criterios de Aceptación (DoD)
- Implementación de `chemical_filters.py`, `formula_estimator.py` y `candidate_db.py`.
- Cobertura de tests unitarios $\ge 85\%$ en los nuevos módulos.
- Aprobación de la suite completa de tests de productos naturales conocidos (alcaloides, flavonoides, glicósidos).
- Auditoría de licencias en `docs/DATA_SOURCES.md` actualizada y conforme con el Hook `H29`.
