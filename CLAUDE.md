# CLAUDE.md — CLI Agent Quick Reference & Developer Guide
# Project: Enveda CASMI 2026 — Molecule ID From Mass Spectra

@AGENTS.md

## Common Commands

### Environment & Setup
- Activate virtualenv: `.venv\Scripts\activate` (Windows) or `source .venv/bin/activate` (Linux/macOS)
- Install dependencies: `pip install -r requirements.txt`
- Install Git hooks: `git config core.hooksPath .agents/git-hooks`

### Running Tests & Hooks
- Run all unit tests: `pytest tests/ -v`
- Run hook acceptance tests: `python .agents/bin/selftest.py`
- Manual pre-commit check: `python .agents/bin/run_checks.py pre-commit`
- Manual pre-push check: `python .agents/bin/run_checks.py pre-push`
- Manual pre-submit check: `python .agents/bin/run_checks.py pre-submit`

### Linting & Formatting
- Lint with Ruff: `ruff check src/ tests/ .agents/hooks/`
- Fix with Ruff: `ruff check --fix src/ tests/ .agents/hooks/`
- Format code: `black src/ tests/ .agents/hooks/`

---

## Architecture & Code Conventions

1. **Python Standard**: Python 3.12, strict type hints (`typing` module / PEP 585 & 604).
2. **Chemoinformatics Rules**:
   - Always standardise molecules to InChIKey14 via `rdMolStandardize.TautomerEnumerator` to match Kaggle scoring.
   - Always calculate neutral mass by explicitly accounting for the adduct (`[M+H]+`, `[M-H]-`, etc.) before formula matching.
   - Never split data on `spectrum_id`; always partition by `molecule_id` using structural clustering (MCES / Murcko scaffold).
3. **No Vibe Coding**:
   - Check `specs/` before creating or editing any production file in `src/`.
   - Complete tasks in `specs/.../tasks.md` sequentially.
   - Write unit tests in `tests/` before marking a task as done `[x]`.
4. **Git, Team Boundaries & Spanish Commits**:
   - **Octavio Luna (Dev 1)**: Data, splits, preprocessing, metrics, validation harness.
   - **Leonardo Ibarra (Dev 2)**: Pilar A (Retrieval / DreaMS) & Pilar B (Fingerprints / MIST / Formula Matching).
   - **Joan Riveros (Dev 3)**: Pilar C (De Novo DiffMS / CFM-ID) & Final Re-ranker (LightGBM).
   - Branch strategy: `main` (prod), `develop` (staging), `test` (benchmark), `product`, `octavio`, `leonardo`, `joan`.
   - **Commits en Español obligatorios**: Conventional Commits en español (ej. `feat(datos): ...`, `fix(metrica): ...`, `test(baseline): ...`).
   - Do not edit modules belonging to another developer without an interface contract change.

