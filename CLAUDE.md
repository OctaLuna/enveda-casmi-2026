# CLAUDE.md — CLI Agent Quick Reference & Developer Guide
# Project: Enveda CASMI 2026 — Molecule ID From Mass Spectra

## Common Commands

### Environment & Setup
- Activate virtualenv: `.venv\Scripts\activate` (Windows) or `source .venv/bin/activate` (Linux/macOS)
- Install dependencies: `pip install -r requirements.txt`
- Install Git hooks: `git config core.hooksPath .githooks`

### Running Tests
- Run all tests: `pytest tests/ -v`
- Run single test file: `pytest tests/test_data.py -v`
- Run single test function: `pytest tests/test_metrics.py -k test_mrr_at_25 -v`
- Run with test coverage: `pytest tests/ --cov=src --cov-report=term-missing`

### Linting & Formatting
- Lint with Ruff: `ruff check src/ tests/`
- Fix with Ruff: `ruff check --fix src/ tests/`
- Format code: `black src/ tests/`
- Flake8 check: `flake8 src/ tests/ --max-line-length=100`

### Validation & Hooks Execution
- Check file sizes before commit: `python .githooks/check_large_files.py`
- Validate SDD task sync: `python -m src.utils.sdd_validator` (when configured)

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
   - Branch strategy: `main` (prod), `develop` (staging), `test` (benchmark), `dev/octavio`, `dev/leonardo`, `dev/joan`.
   - **Commits en Español obligatorios**: Conventional Commits en español (ej. `feat(datos): ...`, `fix(metrica): ...`, `test(baseline): ...`).
   - Do not edit modules belonging to another developer without an interface contract change.

