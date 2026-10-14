# Índice Unificado de Skills — Proyecto Enveda CASMI 2026

Este directorio (`.agents/skills/`) contiene dos familias complementarias de Skills que conviven en armonía:
1. **Skills de Dominio y Pipeline CASMI 2026** (`casmi-00` a `casmi-14`): Codifican la estrategia quimioinformática, modelos (DreaMS, MIST, DiffMS, CFM-ID) y reglas del certamen Kaggle.
2. **Skills Generales de Gobernanza y Metodología SDD**: Procedimientos de ingeniería de software, validación agnóstica y buenas prácticas de desarrollo.

---

## 1. Skills de Dominio CASMI 2026 (Ordenadas por Fase)

Empieza siempre por `casmi-00-orchestrator`.

| Fase | Skill | Qué cubre |
|---|---|---|
| **Coordinación** | [`casmi-00-orchestrator`](file:///d:/Octa/Documents/Proyects/CASMI/.agents/skills/casmi-00-orchestrator/SKILL.md) | Mapa maestro, cronograma, riesgos, orden de trabajo |
| **Fundamentos y datos** | [`casmi-01-metric-canonicalization`](file:///d:/Octa/Documents/Proyects/CASMI/.agents/skills/casmi-01-metric-canonicalization/SKILL.md) | MRR@25, InChIKey14, RDKit fijo, dedupe del top-25 |
| | [`casmi-02-spectra-preprocessing`](file:///d:/Octa/Documents/Proyects/CASMI/.agents/skills/casmi-02-spectra-preprocessing/SKILL.md) | Limpieza, deisotopado, transformación, dedupe |
| | [`casmi-03-adduct-formula`](file:///d:/Octa/Documents/Proyects/CASMI/.agents/skills/casmi-03-adduct-formula/SKILL.md) | m/z → masa neutra, fórmula, DBE, valencia |
| | [`casmi-05-candidate-universe`](file:///d:/Octa/Documents/Proyects/CASMI/.agents/skills/casmi-05-candidate-universe/SKILL.md) | PubChem/COCONUT/LOTUS/HMDB indexados por fórmula |
| **Validación** | [`casmi-04-validation-harness`](file:///d:/Octa/Documents/Proyects/CASMI/.agents/skills/casmi-04-validation-harness/SKILL.md) | Split MCES/scaffold, 3 subsets, semillas |
| **Pilar A (Clase 1)** | [`casmi-06-pillar-a-retrieval`](file:///d:/Octa/Documents/Proyects/CASMI/.agents/skills/casmi-06-pillar-a-retrieval/SKILL.md) | DreaMS + FAISS IVF-PQ + entropía espectral |
| | [`casmi-07-multispectrum-fusion`](file:///d:/Octa/Documents/Proyects/CASMI/.agents/skills/casmi-07-multispectrum-fusion/SKILL.md) | Fusión por `molecule_id`, consistencia entre CE |
| **Pilar B (Clase 2)** | [`casmi-08-pillar-b-fingerprint`](file:///d:/Octa/Documents/Proyects/CASMI/.agents/skills/casmi-08-pillar-b-fingerprint/SKILL.md) | MIST + Tanimoto + SIRIUS/COSMIC |
| **Pilar C (Clase 3)** | [`casmi-09-pillar-c-denovo`](file:///d:/Octa/Documents/Proyects/CASMI/.agents/skills/casmi-09-pillar-c-denovo/SKILL.md) | DiffMS, MSNovelist, contingencia tipo MARLIN |
| | [`casmi-10-cycle-consistency`](file:///d:/Octa/Documents/Proyects/CASMI/.agents/skills/casmi-10-cycle-consistency/SKILL.md) | CFM-ID / ICEBERG forward y reranking |
| **Ensamble** | [`casmi-11-ensemble-reranker`](file:///d:/Octa/Documents/Proyects/CASMI/.agents/skills/casmi-11-ensemble-reranker/SKILL.md) | LightGBM/XGBoost, features, MRR@25 |
| **Producción** | [`casmi-12-compute-cascade`](file:///d:/Octa/Documents/Proyects/CASMI/.agents/skills/casmi-12-compute-cascade/SKILL.md) | Cascada Clase 1→2→3 dentro de 9 h |
| | [`casmi-13-kaggle-packaging`](file:///d:/Octa/Documents/Proyects/CASMI/.agents/skills/casmi-13-kaggle-packaging/SKILL.md) | Datasets offline, `submission.csv`, notebook final |
| | [`casmi-14-experiment-tracking`](file:///d:/Octa/Documents/Proyects/CASMI/.agents/skills/casmi-14-experiment-tracking/SKILL.md) | Registro público vs. local por clase y semilla |

*Orden recomendado de construcción*: `01` → `04` → `02` → `03` → `05` → `06` → *(primer submit)* → `08` → `09/10` → `07` → `11` → `12` → `13` → `14`.

---

## 2. Skills Generales de Gobernanza y Metodología SDD

Operan como directivas transversales de calidad de código y gestión de procesos:

| Skill | Archivo | Propósito |
|---|---|---|
| **Data Validator** | [`data-validator.md`](file:///d:/Octa/Documents/Proyects/CASMI/.agents/skills/data-validator.md) | Auditoría de integridad de datasets, valores nulos, paridad y drift. |
| **Model Trainer** | [`model-trainer.md`](file:///d:/Octa/Documents/Proyects/CASMI/.agents/skills/model-trainer.md) | Estructura estándar de bucles de entrenamiento, checkpoints y gestión GPU. |
| **SDD Spec Generator** | [`sdd-spec-generator.md`](file:///d:/Octa/Documents/Proyects/CASMI/.agents/skills/sdd-spec-generator.md) | Redacción de especificaciones funcionales en sintaxis formal EARS. |
| **Code Reviewer** | [`code-reviewer.md`](file:///d:/Octa/Documents/Proyects/CASMI/.agents/skills/code-reviewer.md) | Checklist de revisión: prevención de leakage, tipado estricto y estilo. |
| **Hook Manager** | [`hook-manager.md`](file:///d:/Octa/Documents/Proyects/CASMI/.agents/skills/hook-manager.md) | Gestión y verificación diagnóstica de Git Hooks y Agent Hooks. |
| **Git Branching & Commits** | [`git-branching-commit.md`](file:///d:/Octa/Documents/Proyects/CASMI/.agents/skills/git-branching-commit.md) | Topología de ramas del equipo, flujo PR y commits obligatorios en español. |

---

## 3. Matriz de Convivencia y No Interferencia

1. **Aislamiento de Nombres**: Todas las skills del dominio de la competencia están prefijadas con `casmi-XX-*`, evitando colisiones con directivas globales.
2. **Activación Específica por Frontmatter**: Cada `SKILL.md` define en su `description` un ámbito de activación exclusivo.
3. **Complementariedad**: Cuando una tarea técnica requiere implementación en código, las skills de gobernanza (`sdd-spec-generator.md`, `code-reviewer.md`) dictan *cómo* documentar y revisar el código, mientras que las skills `casmi-*` dictan *qué* algoritmos quimioinformáticos y modelos ejecutar.
