# Enveda CASMI 2026 — Molecule ID From Mass Spectra 🧪🧬

[![Python 3.12](https://img.shields.io/badge/python-3.12-blue.svg)](https://www.python.org/downloads/)
[![RDKit](https://img.shields.io/badge/RDKit-2026.03.3-green.svg)](https://www.rdkit.org/)
[![Metric](https://img.shields.io/badge/Metric-MRR%4025%20(InChIKey14)-orange.svg)](https://www.kaggle.com/)
[![Tests](https://img.shields.io/badge/Tests-17%20passing%20(100%25)-brightgreen.svg)](https://pytest.org/)
[![SDD](https://img.shields.io/badge/Methodology-Spec--Driven%20Development-purple.svg)](specs/)
[![License](https://img.shields.io/badge/License-Proprietary%20%2F%20Competition-red.svg)]()

> **Competición Oficial Kaggle**: [Enveda CASMI 2026 — Molecule ID From Mass Spectra](https://www.kaggle.com/)  
> **Objetivo**: Predecir la estructura molecular 2D (formato SMILES canónico) a partir de espectros de masas en tándem (LC-MS/MS) de productos naturales (plantas y microbios).  
> **Métrica de Evaluación**: Mean Reciprocal Rank @ 25 (**MRR@25**) coincidiendo contra **InChIKey14** canonicalizado por tautómeros con **RDKit 2026.03.3**.  
> **Restricciones de Entorno**: Notebooks de Kaggle, $\le 9$ horas de ejecución, **sin conexión a internet** en la re-evaluación. Archivo de salida: `submission.csv`.

---

## 👥 Equipo de Desarrollo y Roles

| Integrante | Rol en el Proyecto | Dominio de Módulos | Foco Técnico |
|---|---|---|---|
| **Octavio Luna** *(Dev 1)* | **Data Engineering & Validation Lead** | `src/data/`, `src/utils/metrics.py`, `src/utils/reproducibility.py` | Ingesta de `train.parquet`/`test.parquet`, deisotopado explícito, normalización de masa neutra según aducto, split estructural anti-leakage (MCES/Scaffold) en 3 subsets (`Val-Clase1`, `Val-Clase2`, `Val-Clase3`), y cálculo de MRR@25 con InChIKey14. |
| **Leonardo Ibarra** *(Dev 2)* | **Retrieval & Fingerprints Lead** | `src/models/retrieval/`, `src/models/fingerprints/`, `src/models/candidates/` | **Pilar A** (embeddings fundacionales DreaMS, indexación FAISS IVF-PQ para ~2M vectores, similitud espectral y entropía) y **Pilar B** (predictor neuronal MIST, consulta $O(1)$ de candidatos en PubChem/COCONUT/LOTUS/HMDB y matching por Tanimoto blando). |
| **Joan Riveros** *(Dev 3)* | **Generative & Ensemble Lead** | `src/models/generative/`, `src/models/forward/`, `src/models/ensemble/`, `src/api/` | **Pilar C** (generación *de novo* restringida por fórmula con DiffMS, contingencia MARLIN, simulación forward de ciclo-consistencia con CFM-ID/ICEBERG), modelo de re-ranking LightGBM/XGBoost, presupuesto en cascada ($<9\text{h}$) y `submission.csv`. |

---

## 🏛️ Arquitectura Técnica: Cascada de Tres Pilares

```
                       [ LC-MS/MS Query Spectrum (molecule_id) ]
                                          |
                      +-------------------+-------------------+
                      |                                       |
                      v                                       v
         [ Multi-Spectrum Fusion ]               [ Precursor & Adduct Analysis ]
         (Consistencia Energías)                 (Masa Neutra M + Reglas DBE)
                      |                                       |
                      v                                       v
           [ Pilar A: Retrieval ]                 [ Pilar B: Fingerprint Match ]
         (DreaMS + FAISS IVF-PQ)                 (MIST + PubChem/COCONUT/LOTUS)
                      |                                       |
                      +-------------------+-------------------+
                                          |
                                          v (Si baja confianza / sin biblioteca)
                                [ Pilar C: De Novo ]
                             (DiffMS + CFM-ID Forward)
                                          |
                                          v
                              [ Final Re-ranking ]
                           (LightGBM MRR@25 Ensemble)
                                          |
                                          v
                          [ Output: Top-25 SMILES list ]
```

### Clasificación Estratégica del Test Set (~400 Moléculas)
1. **Clase 1 (Fáciles)**: Espectro presente en bibliotecas públicas $\rightarrow$ Recuperación espectral directa DreaMS + FAISS (**Pilar A**).
2. **Clase 2 (Intermedias)**: Estructura conocida en bases de candidatos pero sin espectro público $\rightarrow$ Fingerprint MIST + filtrado por fórmula molecular (**Pilar B**).
3. **Clase 3 (Fantasmas)**: Ausente de cualquier base pública $\rightarrow$ Generación molecular *de novo* con DiffMS guiada por fórmula y reordenamiento forward por ciclo-consistencia con CFM-ID (**Pilar C**).

---

## 🌳 Estrategia de Ramas en Git (Branching Workflow)

El repositorio sigue un modelo adaptado a Machine Learning colaborativo para 3 desarrolladores:

```
[ main ] <========================= (Releases & Submissions verificados)
   ^
   |
[ develop ] <====================== (Integración continua de features)
   ^
   +---------+---------+
   |         |         |
[ test ]     |         |          (Pruebas de estrés offline < 9h y benchmarks)
   ^         |         |
   |         |         |
[ dev/octavio ]        |          (Espacio de trabajo de Octavio Luna - Datos & Validación)
   |         |         |
   |   [ dev/leonardo ]|          (Espacio de trabajo de Leonardo Ibarra - Retrieval & MIST)
   |         |         |
   |         |   [ dev/joan ]     (Espacio de trabajo de Joan Riveros - Generativo & Ensamble)
   |         |         |
   v         v         v
feature/sprint<N>-<dev>-<nombre>  (Ramas atómicas de trabajo por tarea SDD)
```

### Reglas Innegociables de Git:
1. **`main` y `develop` están protegidas**: Prohibido hacer commits directos (`push origin main/develop`).
2. **Convención de Commits**: Se exige sintaxis Conventional Commits (`feat(...)`, `fix(...)`, `test(...)`, `chore(...)`).
3. **Git Hooks Activos**:
   - `pre-commit`: Valida linters (Ruff, Black), sintaxis Markdown y bloquea archivos pesados $> 50\text{ MB}$, `.parquet` o `.pt`.
   - `pre-push`: Ejecuta la suite de pruebas automatizadas (`pytest tests/ -v`) antes de autorizar envíos remotos.

---

## 📁 Estructura del Repositorio

```text
CASMI/
├── .agents/                 # Gobernanza agéntica, skills operativas y hooks de IA
│   ├── rules/               # Reglas modulares (SDD, Git workflow, commit policy)
│   ├── skills/              # 15 skills del Masterplan CASMI + 5 de metodología SDD
│   └── hooks/               # Hooks de IA (post-task-hook, spec-sync-hook)
├── .githooks/               # Git Hooks pre-commit y pre-push ejecutables
├── docs/
│   ├── constitution.md      # 6 principios innegociables del proyecto
│   └── scrum/               # Planificación de 4 Sprints para Octavio, Leonardo y Joan
├── specs/                   # Especificaciones SDD (spec.md, plan.md, tasks.md)
│   └── 001_model_baseline/  # Feature baseline: ingesta, filtros, splits e InChIKey14
├── data/                    # Datasets locales (ignorado en git)
│   ├── raw/                 # train.parquet y test.parquet originales
│   ├── processed/           # Espectros limpios y desisotopados
│   └── splits/              # Particiones anti-leakage Val-Clase1/2/3 con 3 semillas
├── models/                  # Checkpoints inmutables, índices FAISS y pesos (ignorado en git)
├── src/                     # Código fuente de producción desacoplado
│   ├── data/                # Ingesta, deisotopado y normalización por aductos
│   ├── models/              # Retrieval (Pilar A), Fingerprints (Pilar B), De Novo (Pilar C)
│   ├── utils/               # Cálculo exacto de MRR@25, InChIKey14 y reproducibilidad
│   └── api/                 # Cascada de inferencia y validador de submission.csv
├── tests/                   # Suite de pruebas unitarias TDD (Pytest)
├── AGENTS.md                # Arnés de memoria agnóstico para cualquier agente de IA
├── CLAUDE.md                # Configuración y comandos rápidos CLI
├── requirements.txt         # Dependencias ancladas (Python 3.12, RDKit, PyTorch, FAISS)
└── README.md                # Documentación maestra del proyecto
```

---

## 🚀 Inicio Rápido y Comandos

### 1. Configuración del Entorno
```bash
# Crear y activar entorno virtual
python -m venv .venv
source .venv/bin/activate       # En Linux/macOS
.venv\Scripts\Activate.ps1       # En Windows PowerShell

# Instalar dependencias
pip install -r requirements.txt

# Activar Git Hooks locales
git config core.hooksPath .githooks
```

### 2. Ejecución de Pruebas y Calidad de Código
```bash
# Correr toda la suite de tests (17 tests)
pytest tests/ -v

# Correr tests con reporte de cobertura
pytest tests/ --cov=src --cov-report=term-missing

# Verificación de linting y formato
ruff check src/ tests/
black --check src/ tests/

# Probar validador de archivos grandes manualmente
python .githooks/check_large_files.py
```

---

## 🎯 Cronograma de Sprints (Octubre - Diciembre 2026)

* **Sprint 1 (14 Oct - 28 Oct)**: Ingesta, limpieza espectral, split anti-leakage (MCES/Scaffold), InChIKey14 y baseline inicial.
* **Sprint 2 (29 Oct - 11 Nov)**: Pilar A (DreaMS + FAISS IVF-PQ) y Pilar B (MIST + Matching Fórmula).
* **Sprint 3 (12 Nov - 25 Nov)**: Pilar C (DiffMS De Novo + MARLIN + CFM-ID Forward) y Fusión Multi-Espectro.
* **Sprint 4 (26 Nov - 14 Dic)**: Ensamble LightGBM, optimización de cascada ($<9\text{h}$), empaquetado offline y envíos finales.
* **7 de Diciembre de 2026**: Cierre de fusiones e inscripción de equipos en Kaggle.
* **14 de Diciembre de 2026 (11:59 PM UTC)**: Cierre definitivo de la competencia.
