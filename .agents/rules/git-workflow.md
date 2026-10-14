# Agent Rule: Collaborative Git Workflow for 3 Developers
**Path**: `.agents/rules/git-workflow.md`  
**Scope**: Dev 1, Dev 2, Dev 3 and AI pair programmers.

## Rule Directives
1. **Module Ownership Boundaries**:
   - **Dev 1**: Owns `src/data/`, `src/utils/metrics.py`, `src/utils/reproducibility.py`, and data unit tests.
   - **Dev 2**: Owns `src/models/retrieval/`, `src/models/fingerprints/`, and Pilar A/B pipelines.
   - **Dev 3**: Owns `src/models/generative/`, `src/models/ensemble/`, and `src/api/submission.py`.
2. **Interface Contracts**:
   - Changes across boundaries require an agreed interface defined in `src/models/interfaces.py` or `specs/`.
3. **Branching Strategy**:
   - Main branch is protected: `main`.
   - Feature branches: `feature/sprint<N>-<dev>-<topic>`.
   - Before opening PR, rebase on latest `main` and execute `pytest tests/ -v`.
