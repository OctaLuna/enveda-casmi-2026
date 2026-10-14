# Regla de Agente: Flujo de Trabajo Colaborativo en Git y Commits en Español
**Path**: `.agents/rules/git-workflow.md`  
**Alcance**: Octavio Luna (Dev 1), Leonardo Ibarra (Dev 2), Joan Riveros (Dev 3) y Agentes de IA.

## Directivas Obligatorias

1. **Mensajes de Commit en Español**:
   - Todo mensaje de commit generado por un agente o desarrollador debe redactarse estrictamente en **ESPAÑOL** bajo la convención *Conventional Commits*: `<tipo>(<ámbito>): <descripción en español en imperativo>`.
   - Tipos: `feat`, `fix`, `test`, `refactor`, `perf`, `docs`, `chore`.

2. **Propiedad de Módulos**:
   - **Octavio Luna (Dev 1)**: Propietario de `src/data/`, `src/utils/metrics.py`, `src/utils/reproducibility.py` y tests de datos.
   - **Leonardo Ibarra (Dev 2)**: Propietario de `src/models/retrieval/`, `src/models/fingerprints/` y pipelines de Pilares A y B.
   - **Joan Riveros (Dev 3)**: Propietario de `src/models/generative/`, `src/models/ensemble/` y `src/api/submission.py`.

3. **Estrategia de Ramas**:
   - Ramas protegidas: `main` (producción) y `develop` (integración).
   - Rama de pruebas: `test`.
   - Ramas de trabajo de desarrollador: `dev/octavio`, `dev/leonardo`, `dev/joan`.
   - Ramas de características: `feature/sprint<N>-<dev>-<nombre>`.

4. **Contratos e Interfaces**:
   - Cambios que crucen fronteras de módulo requieren acuerdo previo tipado en `src/models/interfaces.py` y especificación aprobada en `specs/`.

5. **Cero Bypass de Hooks**:
   - Jamás utilizar `--no-verify`. Si un hook rechaza un commit o push, corregir el código subyacente.
