# Marco de Trabajo Ágil & Planificación SCRUM CASMI 2026
## Hoja de Ruta Octubre - Diciembre 2026 (Equipo de 3 Desarrolladores)

---

## 1. Definición del Equipo y Propiedad de Módulos

Para garantizar velocidad y cero conflictos en Git (*merge conflicts*), cada desarrollador tiene un dominio de código asignado con interfaces estrictamente desacopladas:

| Rol | Desarrollador | Dominio Principal de Código | Responsabilidades Clave |
|---|---|---|---|
| **Data & Validation Lead** | **Octavio Luna** *(Dev 1)* | `src/data/`, `src/utils/metrics.py`, `src/utils/reproducibility.py` | Ingesta de `train.parquet`/`test.parquet`, deisotopado, normalización de masa neutra según aducto, split estructural anti-leakage (MCES/Scaffold) para las 3 clases, y cálculo exacto de MRR@25 con canonicalización InChIKey14. |
| **Retrieval & Fingerprints Lead** | **Leonardo Ibarra** *(Dev 2)* | `src/models/retrieval/`, `src/models/fingerprints/`, `src/models/candidates/` | Pilar A (Embeddings DreaMS, indexación FAISS IVF-PQ, similitud espectral y entropía) y Pilar B (Predictor neuronal MIST, consulta de universos de candidatos PubChem/COCONUT/LOTUS/HMDB y matching por Tanimoto). |
| **Generative & Ensemble Lead** | **Joan Riveros** *(Dev 3)* | `src/models/generative/`, `src/models/forward/`, `src/models/ensemble/`, `src/api/` | Pilar C (Generador DiffMS de novo, salvaguarda MARLIN, ciclo-consistencia CFM-ID/ICEBERG), modelo de re-ranking LightGBM/XGBoost, presupuesto de inferencia en cascada (<9h) y pipeline de `submission.csv`. |

---

## 2. Calendario de Sprints hacia el Deadline Final

* **Fecha de Inicio de Planificación**: 14 de Octubre de 2026.
* **Cierre de Equipos & Fusiones en Kaggle**: 7 de Diciembre de 2026.
* **Deadline Definitivo de Entrega**: 14 de Diciembre de 2026 (11:59 PM UTC).

```
[14 Oct] === Sprint 1 ===> [28 Oct] === Sprint 2 ===> [11 Nov] === Sprint 3 ===> [25 Nov] === Sprint 4 ===> [14 Dic]
         Datos, Splits,            Pilar A (DreaMS/FAISS)    Pilar C (DiffMS/CFM)      Ensamble LightGBM
         InChIKey14 & Baseline     Pilar B (MIST/Fórmula)    Fusión Multi-Espectro     Inferencia Cascada <9h
                                                                                       Kaggle Submissions
```

---

## 3. Protocolo de Git y Prevención de Merge Conflicts

1. **Ramas Troncales**:
   - `main`: Producción oficial y submissions finales verificadas (protegida).
   - `develop`: Integración continua de features completadas (protegida).
   - `test`: Banco de pruebas de estrés offline y benchmarks de 9 horas.
   - `product`: Congelamiento y validación para el artefacto final de Kaggle.
2. **Ramas de Desarrollador**:
   - `octavio` (Octavio Luna)
   - `leonardo` (Leonardo Ibarra)
   - `joan` (Joan Riveros)
3. **Nomenclatura de Feature Branches**:
   - `feature/sprint<N>-octavio-<feature>`
   - `feature/sprint<N>-leonardo-<feature>`
   - `feature/sprint<N>-joan-<feature>`
4. **Contratos de Interfaz Tipados**:
   - Leonardo y Joan consumen los objetos de espectro generados por Octavio a través de dataclasses compartidas (`SpectrumRecord`, `CandidateMatch`).
   - Joan consume las listas de candidatos de Leonardo mediante la interfaz estandarizada `RankedCandidate`.
5. **Integración Continua Local**:
   - Todo PR hacia `develop` exige la aprobación de al menos otro desarrollador y la ejecución exitosa de los hooks `pre-commit` y `pre-push`.

---

## 4. Ceremonias Ágiles Adaptadas
- **Daily Standup Asíncrono (10 min)**: Qué completé ayer, qué haré hoy, qué me bloquea.
- **Sprint Planning (Inicio de Sprint)**: Refinamiento de `tasks.md` en sintaxis SDD y ajuste de dependencias.
- **Sprint Review & Leaderboard Sync (Fin de Sprint)**: Evaluación de MRR@25 local en los 3 subsets vs. envío de calibración a Kaggle.

