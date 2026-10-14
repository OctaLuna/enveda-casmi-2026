# Sprint 3: Pilar C (Generación De Novo DiffMS + Cycle-Consistency) y Fusión Multi-Espectro
**Período**: 12 de Noviembre de 2026 – 25 de Noviembre de 2026 (Semanas 5 y 6)  
**Meta del Sprint**: Dominar la Clase 3 ("Moléculas Fantasma") mediante generación *de novo* restringida por fórmula química con DiffMS, incorporar el plan de contingencia MARLIN para fórmulas inciertas, implementar la verificación forward por ciclo-consistencia (CFM-ID/ICEBERG), y aplicar fusión multi-espectro por `molecule_id`.

---

## 1. Reparto Equitativo de Tareas

### Dev 1: Lead de Fusión Multi-Espectro y Datos de Preentrenamiento
* **Módulos**: `src/data/multi_spectrum_fusion.py`, `src/data/collision_energy_analyzer.py`
* **Tareas Asignadas**:
  1. `[DEV1-3.1]` Implementar agregador multi-espectro en `src/data/multi_spectrum_fusion.py`: promediar embeddings y alinear espectros de todos los `spectrum_id` correspondientes a un mismo `molecule_id` ponderando por número de picos y relación señal/ruido.
  2. `[DEV1-3.2]` Desarrollar analizador de persistencia de picos a través de energías de colisión en `src/data/collision_energy_analyzer.py` para aislar subestructuras robustas y confirmar fórmula.
  3. `[DEV1-3.3]` Preparar dataset offline curado de pares fingerprint-estructura (DSSTox, COCONUT, LOTUS) para nutrir el decodificador de DiffMS.

### Dev 2: Lead de Contingencia MARLIN y Generador De Novo
* **Módulos**: `src/models/generative/marlin_fallback.py`, `src/models/generative/diffms_adapter.py`
* **Tareas Asignadas**:
  1. `[DEV2-3.1]` Implementar salvaguarda tipo **MARLIN** en `src/models/generative/marlin_fallback.py`: reentrenar o ajustar la cabeza del predictor MIST para emitir secuencias moleculares directamente sin depender de una fórmula molecular garantizada.
  2. `[DEV2-3.2]` Integrar el encoder de DiffMS (`coleygroup/DiffMS`) acoplándolo con los fingerprints de MIST y restricciones estequiométricas.
  3. `[DEV2-3.3]` Desarrollar lógica de decisión que activa DiffMS si la fórmula tiene alta confianza, o MARLIN si el error de masa o patrón isotópico es ambiguo.

### Dev 3: Lead de Decodificador de Difusión y Verificación Forward (Cycle-Consistency)
* **Módulos**: `src/models/generative/diffms_decoder.py`, `src/models/forward/cfmid_verifier.py`
* **Tareas Asignadas**:
  1. `[DEV3-3.1]` Configurar e inferir el decodificador de difusión discreta sobre grafos moleculares de **DiffMS**, generando hasta 50 candidatos estructurales válidos por molécula fantasma.
  2. `[DEV3-3.2]` Implementar el verificador forward de ciclo-consistencia en `src/models/forward/cfmid_verifier.py`: simular el espectro teórico MS/MS de cada candidato generado utilizando **CFM-ID** o **ICEBERG**.
  3. `[DEV3-3.3]` Calcular la similitud espectral entre el espectro teórico simulado y el espectro real observado para reordenar la lista de candidatos de novo.
  4. `[DEV3-3.4]` Evaluar el rendimiento en `Val-Clase3` y documentar ganancias de MRR@25 respecto a métodos aleatorios.

---

## 2. Mapa de Dependencias y Mitigación de Bloqueos

```
[Inicio Sprint]
  Dev 1: Fusión multi-espectro (alimenta a Pilares A, B y C)
  Dev 2: Pipeline de decisión fórmula vs. MARLIN
  Dev 3: Decodificador DiffMS + Simulación CFM-ID
       |
[Día 5] Dev 1 provee espectros fusionados a nivel molecule_id
       |
       v
  Dev 2 & Dev 3 prueban generación de novo sobre espectros fusionados
       |
[Día 8] Candidatos DiffMS generados pasan al verificador CFM-ID de Dev 3
       |
       v
[Día 10] Benchmark conjunto en Val-Clase3 con cycle-consistency scoring
```

---

## 3. Criterio de Aceptación del Sprint (DoD)
- La fusión multi-espectro reduce la varianza espectral y mejora el MRR@25 de Pilar A y B en al menos un 5% relativo.
- DiffMS genera 100% de estructuras químicas químicamente válidas (sin errores de valencia en RDKit).
- La verificación forward por ciclo-consistencia (CFM-ID) mejora el ranking del candidato correcto en el top 25 de la Clase 3.
- Todo el código opera bajo la suite de tests automatizada.

