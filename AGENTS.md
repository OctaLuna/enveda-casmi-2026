# AGENTS.md — Global AI Agent Governance & Operational Harness
# Project: Enveda CASMI 2026 — Molecule ID From Mass Spectra

> **Agnostic Standard**: This governance and memory harness applies to all autonomous AI agents (Google Antigravity, Claude Code, OpenAI Codex, OpenCode, Cursor Agent, GitHub Copilot Workspace).

---

## 1. Project Overview & North Star

* **Competition**: Enveda CASMI 2026 — Molecule ID From Mass Spectra (Kaggle).
* **Objective**: Predict 2D molecular structures (canonical SMILES) from tandem mass spectrometry (LC-MS/MS) spectra of natural products (plants and microbes).
* **Evaluation Metric**: Mean Reciprocal Rank @ 25 (**MRR@25**). Each prediction must contain up to 25 ranked candidate SMILES per `molecule_id` separated by `;`.
* **Matching Ground Truth**: Predictions and ground truth are canonicalized via tautomers using **RDKit 2026.03.3** (`rdMolStandardize.TautomerEnumerator`) and matched against the first 14 characters of InChIKey (**InChIKey14**). No penalty for stereocenters or tautomeric representations.
* **Environment Constraints**: Kaggle Notebooks, max **9 hours** execution, **no internet access** during evaluation submission, output file `submission.csv`.
* **Team Structure**: 3 Developers (Dev 1: Data Engineering & Validation Lead, Dev 2: Search, Retrieval & Fingerprint Lead, Dev 3: De Novo Generation & Ensembling Lead).

---

## 2. Technical Stack & Standards

* **Language**: Python 3.12+ (standardized across local and Kaggle runtimes).
* **Core Chemoinformatics**: RDKit (`rdkit>=2024.3.1`, targeting matching behavior of `2026.03.3`), `matchms`, `molvs`.
* **Deep Learning & Embeddings**: PyTorch (`torch>=2.2.0`), DreaMS backbone, MIST, DiffMS.
* **Vector Indexing**: FAISS (IVF-PQ indexing for 2M+ spectral vectors).
* **Tabular ML & Ensembling**: LightGBM, XGBoost, Scikit-Learn.
* **Experiment Tracking**: MLflow (local tracking server, decoupled from git).
* **Quality & Testing**: Pytest, Pytest-cov, Ruff, Black, Flake8.

---

## 3. Architecture Blueprint (Three-Pillar Cascade)

```
                       [ LC-MS/MS Query Spectrum (molecule_id) ]
                                          |
                      +-------------------+-------------------+
                      |                                       |
                      v                                       v
         [ Multi-Spectrum Fusion ]               [ Precursor & Adduct Analysis ]
                      |                                       |
                      v                                       v
           [ Pilar A: Retrieval ]                 [ Exact Neutral Mass + DBE ]
         (DreaMS + FAISS IVF-PQ)                              |
                      |                                       v
                      |                         [ Pilar B: Fingerprint Match ]
                      |                         (MIST + PubChem/COCONUT/LOTUS)
                      |                                       |
                      +-------------------+-------------------+
                                          |
                                          v (If low confidence / novel)
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

---

## 4. Agnostic Agent Rules & "No Vibe Coding" Directive

Every agent interacting with this repository MUST adhere to the following non-negotiable protocols:

1. **Strict Spec-Driven Development (SDD)**:
   - NEVER create or modify production code in `src/` without an approved specification in `specs/`.
   - Workflow order: `spec.md` (EARS requirements) -> `plan.md` (technical design) -> `tasks.md` (atomic tasks <30m) -> `tests/` (TDD unit test) -> `src/` (implementation).
2. **Reproducibility & Seed Lockdown**:
   - Every stochastic operation must be seeded using `src.utils.reproducibility.set_seed(42)`.
   - Never use non-deterministic random splits. Validation splits must be stratified and structural (MCES / Murcko scaffold).
3. **Data Protection & Artifact Boundaries**:
   - Never commit files > 50MB, `.parquet`, `.pt`, `.pkl`, or raw spectra to Git.
   - Clean data must never touch raw data in place; transformations must output to `data/processed/` or `data/splits/`.
4. **Git Harmony for 3 Developers**:
   - Each developer works on assigned modules with defined interfaces:
     - **Dev 1**: `src/data/`, `src/utils/metrics.py`, `src/utils/reproducibility.py`.
     - **Dev 2**: `src/models/retrieval/`, `src/models/fingerprints/`.
     - **Dev 3**: `src/models/generative/`, `src/models/ensemble/`, `src/api/submission.py`.
   - Modules communicate via abstract base classes and typed Pydantic / dataclass interfaces to avoid merge conflicts.

---

## 5. Quick Command Reference

```bash
# Setup environment
python -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\Activate.ps1
pip install -r requirements.txt

# Activate Git hooks
git config core.hooksPath .githooks

# Run all unit tests
pytest tests/ -v

# Run fast unit tests with coverage
pytest tests/ --cov=src --cov-report=term-missing

# Code formatting & linting
ruff check src/ tests/
black --check src/ tests/

# Validate pre-commit checks manually
python .githooks/check_large_files.py
```

---

## 6. Directory Layout & Module Responsibilities

```text
CASMI/
├── .agents/                 # Agent memory, skills, hooks and rules
│   ├── rules/               # Modular operational directives
│   ├── skills/              # Agnostic reusable skills (.md)
│   └── hooks/               # Event hooks for agent actions
├── .githooks/               # Git quality hooks (pre-commit, pre-push)
├── docs/
│   ├── constitution.md      # 6 non-negotiable principles
│   └── scrum/               # Sprint backlogs and Dev 1/2/3 assignments
├── specs/                   # Spec-Driven Development (spec, plan, tasks)
├── data/                    # Local datasets (raw, processed, splits - gitignored)
├── models/                  # Checkpoints, indices and weights (gitignored)
├── src/                     # Production source code
│   ├── data/                # Spectrum parsing, filtering, deisotoping, splits
│   ├── models/              # Retrieval, fingerprint matching, de novo, ensemble
│   ├── utils/               # Metrics (MRR@25), InChIKey14, seeds, logging
│   └── api/                 # Inference cascade & submission generator
└── tests/                   # Pytest test suite (unit, integration, regression)
```

