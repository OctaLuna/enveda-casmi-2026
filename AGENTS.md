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
* **Team Structure**: 3 Developers:
  - **Octavio Luna** (Dev 1): Data Engineering & Validation Lead.
  - **Leonardo Ibarra** (Dev 2): Search, Retrieval & Fingerprint Lead.
  - **Joan Riveros** (Dev 3): De Novo Generation & Ensembling Lead.

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
     - **Octavio Luna (Dev 1)**: `src/data/`, `src/utils/metrics.py`, `src/utils/reproducibility.py`.
     - **Leonardo Ibarra (Dev 2)**: `src/models/retrieval/`, `src/models/fingerprints/`.
     - **Joan Riveros (Dev 3)**: `src/models/generative/`, `src/models/ensemble/`, `src/api/submission.py`.
   - Modules communicate via abstract base classes and typed Pydantic / dataclass interfaces to avoid merge conflicts.
5. **Mandatory Commits in Spanish**:
   - All Git commit messages generated by humans or AI agents MUST be in **SPANISH** following Conventional Commits (`feat(datos): ...`, `fix(metrica): ...`, `test(baseline): ...`, `docs(scrum): ...`).

---

## 5. Quick Command Reference & Hooks Verification

```bash
# Setup environment
python -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\Activate.ps1
pip install -r requirements.txt

# Activate Git hooks (multi-agent governance)
git config core.hooksPath .agents/git-hooks

# Run multi-agent hook acceptance tests (offline, stdlib)
python .agents/bin/selftest.py

# Manual verification checks (pre-commit, pre-push, pre-submit)
python .agents/bin/run_checks.py pre-commit
python .agents/bin/run_checks.py pre-push
python .agents/bin/run_checks.py pre-submit

# Run all unit tests
pytest tests/ -v

# Code formatting & linting
ruff check src/ tests/ .agents/hooks/
black --check src/ tests/ .agents/hooks/
```

---

## 6. Directory Layout & Module Responsibilities

```text
CASMI/
├── .agents/                 # Centralized agent memory, hooks, skills, rules, and adapters
│   ├── project.json         # Single source of truth for CASMI invariants
│   ├── bin/                 # agent-hook dispatcher, selftest.py, run_checks.py
│   ├── hooks/               # H01–H52 python hooks (safety, domain, context, quality, logging)
│   ├── git-hooks/           # G01–G06 git hooks (pre-commit, commit-msg, pre-push, etc.)
│   ├── rules/               # Persistent context rules (casmi-invariantes, offline, etc.)
│   ├── workflows/           # /pre-submit, /new-experiment, /pre-pr
│   ├── skills/              # 15 masterplan domain skills + SDD skills
│   ├── adapters/            # Claude Code, Codex, and Antigravity templates and notes
│   ├── state/               # session-notes.md, activity.log (gitignored)
│   └── tests/               # Fixtures and acceptance tests for selftest.py
├── .claude/                 # Claude Code configuration (settings.json)
├── .codex/                  # OpenAI Codex configuration (config.toml)
├── .github/                 # CI workflows, PR and Issue templates, CODEOWNERS
├── docs/                    # Constitution, Scrum boards, DATA_SOURCES.md
├── specs/                   # Spec-Driven Development (spec, plan, tasks)
├── data/                    # Local datasets (raw, processed, splits - gitignored)
├── models/                  # Checkpoints, indices and weights (gitignored)
├── src/                     # Production source code (data, models, utils, api)
└── tests/                   # Pytest test suite (unit, integration, regression)
```

