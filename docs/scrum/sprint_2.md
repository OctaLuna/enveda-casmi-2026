# Sprint 2: Pilar A (DreaMS + FAISS IVF-PQ) y Pilar B (MIST + Fórmulas + Matching)
**Período**: 29 de Octubre de 2026 – 11 de Noviembre de 2026 (Semanas 3 y 4)  
**Meta del Sprint**: Poner en producción los motores de recuperación de Clase 1 y Clase 2: Pilar A con embeddings fundacionales DreaMS y FAISS IVF-PQ para ~2M de vectores; Pilar B con estimación de fórmula molecular, predictor MIST de fingerprints y matching Tanimoto sobre PubChem, COCONUT, LOTUS y HMDB.

---

## 1. Reparto Equitativo de Tareas

### Dev 1: Lead de Química Computacional y Universo de Candidatos
* **Módulos**: `src/data/formula_estimator.py`, `src/data/candidate_db.py`, `src/data/chemical_filters.py`
* **Tareas Asignadas**:
  1. `[DEV1-2.1]` Implementar estimador de fórmula molecular exacta en `src/data/formula_estimator.py` a partir de masa neutra (corregida por aducto) y ratios de picos isotópicos con ventana de 5-10 ppm.
  2. `[DEV1-2.2]` Desarrollar filtros de restricciones químicas en `src/data/chemical_filters.py`: validación de reglas de valencia atómica de Senior y cálculo de grado de insaturación DBE (*Double Bond Equivalents*).
  3. `[DEV1-2.3]` Construir indexador local offline de bases de candidatos (PubChem, COCONUT, LOTUS, HMDB) particionado por fórmula molecular exacta para consulta $O(1)$.
  4. `[DEV1-2.4]` Implementar suite de tests para fórmulas complejas de productos naturales (alcaloides, flavonoides, glicósidos).

### Dev 2: Lead de Embeddings Fundacionales e Indexación Vectorial (Pilar A)
* **Módulos**: `src/models/retrieval/dreams_encoder.py`, `src/models/retrieval/faiss_index.py`
* **Tareas Asignadas**:
  1. `[DEV2-2.1]` Integrar arquitectura y pesos preentrenados del modelo fundacional **DreaMS** en `src/models/retrieval/dreams_encoder.py`.
  2. `[DEV2-2.2]` Implementar pipeline de fine-tuning ligero de DreaMS sobre el conjunto de entrenamiento de Enveda (loss de contraste entre espectros del mismo `molecule_id`).
  3. `[DEV2-2.3]` Construir índice vectorial **FAISS IVF-PQ** (ej. `IVF4096,PQ64`) para indexar los ~2 millones de espectros de train con compresión de memoria para caber en RAM de Kaggle.
  4. `[DEV2-2.4]` Benchmark del Pilar A sobre `Val-Clase1`: optimizar top-k y umbral de confianza por distancia coseno.

### Dev 3: Lead de Predicción de Fingerprints y Matching Estructural (Pilar B)
* **Módulos**: `src/models/fingerprints/mist_predictor.py`, `src/models/fingerprints/tanimoto_ranker.py`, `src/models/fingerprints/sirius_bridge.py`
* **Tareas Asignadas**:
  1. `[DEV3-2.1]` Integrar predictor neuronal de fingerprints **MIST** en `src/models/fingerprints/mist_predictor.py` para mapear espectro MS/MS a vector de subestructuras moleculares.
  2. `[DEV3-2.2]` Implementar motor de ranking de similitud de Tanimoto en `src/models/fingerprints/tanimoto_ranker.py` entre el fingerprint predicho por MIST y los fingerprints reales de los candidatos filtrados por fórmula.
  3. `[DEV3-2.3]` Crear puente de extracción de score de confianza COSMIC de SIRIUS 6 / CSI:FingerID para complementar la predicción de MIST.
  4. `[DEV3-2.4]` Validar y reportar MRR@25 del Pilar B en `Val-Clase2` (estructuras conocidas sin espectro en biblioteca).

---

## 2. Mapa de Dependencias y Mitigación de Bloqueos

```
[Inicio Sprint]
  Dev 1: Desarrolla formula_estimator.py & candidate_db.py
  Dev 2: Descarga DreaMS y configura FAISS IVF-PQ (Independiente)
  Dev 3: Configura inferencia MIST y ranking Tanimoto
       |
[Día 5] Dev 1 entrega índice de candidatos por fórmula
       |
       v
  Dev 3 conecta MIST con candidatos de Dev 1 -> Pilar B funcional
       |
[Día 9-10] Integración Pilar A (Dev 2) + Pilar B (Dev 3) evaluados en Val-Clase1 y Val-Clase2
```

---

## 3. Criterio de Aceptación del Sprint (DoD)
- Índice FAISS IVF-PQ ocupa $< 3$ GB de RAM y responde consultas top-25 en $< 15$ ms por espectro.
- Pilar A supera MRR@25 de 0.60 en `Val-Clase1`.
- Pilar B genera lista ordenada de 25 candidatos para cualquier fórmula molecular válida en $< 1.5$ s por consulta.
- Todos los componentes corren de forma determinista y offline con tests pasando al 100%.

