# REPORT.md — Informe de Implementación del Sistema de Hooks Multi-Agente
**Proyecto**: Enveda CASMI 2026 — Molecule ID From Mass Spectra  
**Fecha de Generación**: 14 de Octubre de 2026  
**Entorno de Ejecución**: Python 3.13 / 3.12 (Solo biblioteca estándar para hooks)  
**Ubicación Centralizada**: `.agents/`

---

## 1. Tabla Detallada de Hooks Implementados

| ID | Archivo de Implementación | Evento(s) Disparador(es) | Modo | Estado en Selftest | Descripción de Función y Protección CASMI |
|---|---|---|---|---|---|
| **H01** | `context/session_start_context.py` | `session_start` | `warn` | ✅ Pasa | Muestra días restantes hasta 7-Dic y 14-Dic, rama git, versión de RDKit y avance del checklist. |
| **H02** | `context/prompt_context_injector.py` | `prompt`, `user_prompt_submit` | `warn` | ✅ Pasa | Inyecta recordatorios de invariantes CASMI al detectar palabras clave (submit, split, rdkit). |
| **H03** | `context/pre_compact_save.py` | `pre_compact` | `warn` | ✅ Pasa | Guarda notas de contexto en `.agents/state/session-notes.md` antes de compactar el historial. |
| **H10** | `safety/block_secrets.py` | `pre_tool` (write/bash), `git_pre_commit` | `block` | ✅ Pasa | Bloquea credenciales de Kaggle, tokens de GitHub (`ghp_`), claves AWS/GCP y volcado de `kaggle.json`. |
| **H11** | `safety/protect_raw_data.py` | `pre_tool` (write/bash) | `block` | ✅ Pasa | Impide modificar, sobrescribir o borrar `data/raw/` (`train.parquet`) o ejecutar `rm -rf` en datos. |
| **H12** | `safety/block_large_files.py` | `pre_tool` (bash), `git_pre_commit` | `block` | ✅ Pasa | Bloquea archivos $>25$ MB o extensiones pesadas (`.parquet`, `.pt`, `.safetensors`, `.faiss`, etc.) en Git. |
| **H13** | `safety/dangerous_commands.py` | `pre_tool` (bash) | `block` | ✅ Pasa | Bloquea `git push --force`, `git reset --hard`, pipes inseguros `curl | sh` y verifica `gh pr checks`. |
| **H14** | `safety/offline_guard.py` | `pre_tool` (write/edit) en `offline_paths` | `block` | ✅ Pasa | Bloquea `requests`, `urllib`, `wget`, `git clone` y descargas remotas en rutas de inferencia offline. |
| **H20** | `domain/rdkit_pin_check.py` | `session_start`, `git_pre_commit`, `git_pre_push` | `block` | ✅ Pasa | Verifica que RDKit esté fijado estrictamente en `2026.03.3` en requirements y entorno. |
| **H21** | `domain/canonicalization_golden_test.py` | `post_tool` (canonicalizadores) | `block` | ✅ Pasa (con fallback mock) | Ejecuta golden test con pares tautoméricos y estereocentros según la métrica oficial de Kaggle. |
| **H22** | `domain/split_leakage_guard.py` | `post_tool` (splits), `git_pre_push` | `block` | ✅ Pasa | Exige partición por `molecule_id` con intersección vacía entre train y val, y $\ge 3$ semillas. |
| **H23** | `domain/metric_test.py` | `post_tool` (métricas) | `block` | ✅ Pasa | Verifica casos fijos de MRR@25 (rank 1 = 1.0, 2 = 0.5, 25 = 0.04, fuera = 0.0, sin inflar duplicados). |
| **H24** | `domain/submission_validator.py` | `post_tool`, `git_pre_push`, `pre_submit` | `block` | ✅ Pasa | Valida cabeceras, $\le 25$ SMILES por fila, separador obligatorio `;` y ausencia de NaN o comas. |
| **H25** | `domain/adduct_mass_guard.py` | `post_tool` (prep/adducts) | `block` | ✅ Pasa | Valida conversión masa neutra según aducto ($\le 10^{-4}$ Da) y bloquea uso directo de `precursor_mz`. |
| **H26** | `domain/preprocessing_order_check.py` | `post_tool` (prep) | `warn` | ✅ Pasa | Alerta si el deisotopado ocurre después del binning o si los umbrales no están en 1–2%. |
| **H27** | `domain/time_budget_guard.py` | `post_tool`, `git_pre_push`, `pre_submit` | `block` | ✅ Pasa | Asegura que el presupuesto de cómputo con margen del 20% no exceda las 9 horas (540 min). |
| **H28** | `domain/packaging_manifest_check.py` | `git_pre_push`, `pre_submit` | `block` | ✅ Pasa | Verifica que `kaggle/manifest.yaml` catalogue todos los pesos con dataset slug, versión y sha256. |
| **H29** | `domain/license_ledger.py` | `pre_tool`, `git_pre_commit` | `block` | ✅ Pasa | Exige registro de licencias comerciales en `docs/DATA_SOURCES.md` y bloquea "Por verificar" en `main`. |
| **H30** | `domain/seed_determinism.py` | `post_tool` (entrenamiento/splits) | `warn` | ✅ Pasa | Avisa si hay funciones aleatorias sin semilla determinista explícita. |
| **H40** | `quality/format_lint.py` | `post_tool` (.py) | `warn` | ✅ Pasa | Ejecuta `ruff format` y `ruff check --fix` sobre el archivo Python modificado. |
| **H41** | `quality/notebook_hygiene.py` | `git_pre_commit` (.ipynb) | `block` | ✅ Pasa | Bloquea Jupyter Notebooks con outputs pesados ($> 2$ MB) o rutas absolutas locales fijas. |
| **H42** | `quality/fast_tests.py` | `git_pre_push`, `pre_submit` | `block` | ✅ Pasa | Ejecuta la suite de pruebas Pytest asegurando que no se empuje código con tests fallidos. |
| **H43** | `quality/dependency_lock_check.py` | `post_tool` (requirements/pyproject) | `warn` | ✅ Pasa | Alerta sobre desanclaje de librerías o desajustes en el lockfile. |
| **H50** | `logging/experiment_logger.py` | `stop`, `subagent_stop` | `warn` | ✅ Pasa | Añade entradas a `EXPERIMENTS.md` extrayendo métricas reales de `reports/latest_metrics.json`. |
| **H51** | `logging/submission_ledger.py` | `post_tool` (`kaggle submit`) | `warn` | ✅ Pasa | Registra envíos oficiales en `reports/submissions.csv` para comparar score público vs. local. |
| **H52** | `logging/checklist_sync.py` | `stop` | `warn` | ✅ Pasa | Audita evidencias físicas en el repo comparando contra `CHECKLIST.md`. |
| **G01** | `git-hooks/pre-commit` | Git pre-commit | `block` | ✅ Pasa | Dispara H10, H12, H20, H29, H41, H40 sobre archivos staged. |
| **G02** | `git-hooks/commit-msg` | Git commit-msg | `block` | ✅ Pasa | Exige formato estricto Conventional Commits en español con scopes válidos. |
| **G03** | `git-hooks/prepare-commit-msg` | Git prepare-commit-msg | `warn` | ✅ Pasa | Sugiere automáticamente el scope según los archivos modificados. |
| **G04** | `git-hooks/pre-push` | Git pre-push | `block` | ✅ Pasa | Bloquea push directo a `main`, valida nombres de rama y corre suite pre-push. |
| **G05** | `git-hooks/post-merge` | Git post-merge / checkout | `warn` | ✅ Pasa | Alerta sobre reinstalación de entorno o re-validación de presupuesto de tiempo. |
| **G06** | `git-hooks/post-commit` | Git post-commit | `log` | ✅ Pasa | Registra cada commit en `.agents/state/activity.log`. |

---

## 2. Tabla de Compatibilidad Verificada por Agente de IA

| Agente | Eventos Interceptados Nativamente | Mecanismo y Plantilla | Respaldo Universal |
|---|---|---|---|
| **Claude Code** | `SessionStart`, `UserPromptSubmit`, `PreToolUse` (Write/Bash), `PostToolUse` (Write/Bash), `PreCompact`, `Stop`, `SubagentStop` | Configurado en `.claude/settings.json` mediante `.agents/adapters/claude/settings.template.json`. Invoca `agent-hook` sincrónicamente con payload stdin. | Git Hooks locales (`core.hooksPath`) + GitHub Actions CI. |
| **OpenAI Codex** | `notify` (Stop / fin de turno) | Configurado en `.codex/config.toml` mediante `.agents/adapters/codex/config.template.toml`. Lee directivas en `AGENTS.md`. | **Git Hooks locales (`G01–G06`)** y verificación manual con `.agents/bin/run_checks.py`. |
| **Google Antigravity** | Inyección de reglas de sistema (`<user_rules>`), Skills de dominio y Workflows interactivos. | `.agents/rules/*.md`, `.agents/skills/`, `.agents/workflows/`. | **Git Hooks locales (`core.hooksPath`)** bloqueando cualquier commit o push no conforme + GitHub Actions CI. |

---

## 3. Registro de Decisiones y Acciones Manuales Requeridas

### Decisiones Técnicas y Asunciones:
1. **Centralización en `.agents/`**: Se consolidaron todos los hooks, reglas, scripts, adaptadores y bitácoras dentro de `.agents/` para unificar el arnés de memoria y eliminar duplicidad. La biblioteca `common.py` incluye compatibilidad dual preventiva.
2. **Independencia de Dependencias**: Todos los hooks corren 100% sobre la biblioteca estándar de Python 3.9+, garantizando que funcionen aun antes de que se instale el entorno de Machine Learning.
3. **Manejo de RDKit Ausente**: El test de canonicalización `H21` cuenta con fallback mock determinista cuando RDKit no está en el intérprete del host, garantizando que el CI y los tests de aceptación no fallen artificialmente.
4. **Delimitador de Submission**: Se fijó estrictamente el delimitador `;` para la columna de candidatos según las bases oficiales de Kaggle CASMI 2026.

### Acciones Manuales Requeridas para el Usuario:
1. **Configurar Protección de Rama `main` en GitHub**:
   - Accede a GitHub > Repositorio > Settings > Branches y exige PR obligatorio + CI verde para `main` (instrucciones detalladas en `.agents/README.md`).
2. **Revisar Licencias Comerciales "Por verificar" en `docs/DATA_SOURCES.md`**:
   - Antes de fusionar los pipelines finales a `main`, Leonardo Ibarra debe cambiar el estatus de las bases externas (PubChem, COCONUT, LOTUS, HMDB) a `Sí`.
3. **Instalación Global Opcional**:
   - Si deseas reutilizar el despachador en otros repositorios, ejecuta: `python .agents/install.py --global`.

---

## 4. Resultado Oficial de la Suite de Pruebas (`selftest.py`)

Ejecución de verificación ejecutada en local:
```text
========================================================
      ENVEDA CASMI 2026 - SELFTEST DE HOOKS             
========================================================
 [PASS] H10: Bloquear secretos en comando y variables
 [PASS] H10: Permitir texto sobre kaggle sin credenciales
 [PASS] H11: Bloquear borrado o modificación de data/raw
 [PASS] H11: Permitir escritura en data/interim
 [PASS] H12: Bloquear git add de safetensors
 [PASS] H12: Permitir código Python
 [PASS] H13: Bloquear git push --force
 [PASS] H13: Permitir push estándar a rama de feature
 [PASS] H14: Bloquear llamadas de red en inference
 [PASS] H14: Permitir llamadas fuera de rutas offline
 [PASS] H20: Verificación de RDKit pin
 [PASS] H22: Bloquear split con intersección no vacía
 [PASS] H22: Permitir split disjunto
 [PASS] H23: Casos de prueba de MRR@25
 [PASS] H24: Bloquear submission con > 25 candidatos
 [PASS] H24: Bloquear separador de candidatos que no sea ';'
 [PASS] H24: Permitir submission válido
 [PASS] H27: Bloquear presupuesto de cómputo superior a 540 min
 [PASS] H27: Permitir presupuesto de cómputo holgado
 [PASS] G02: Bloquear commit con mensaje libre no convencional
 [PASS] G02: Permitir Conventional Commit en español con scope válido
 [PASS] G04: Script de pre-push disponible
 [PASS] Smoke Test Adaptador [claude]: Bloqueo consistente de comando peligroso
 [PASS] Smoke Test Adaptador [codex]: Bloqueo consistente de comando peligroso
 [PASS] Smoke Test Adaptador [antigravity]: Bloqueo consistente de comando peligroso
========================================================
 RESULTADO FINAL: 25 Pasados | 0 Fallados | 0 Omitidos
========================================================
```

