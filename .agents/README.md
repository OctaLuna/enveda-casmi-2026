# Sistema de Hooks Multi-Agente — Enveda CASMI 2026
**Ubicación**: `.agents/`

Este directorio contiene la infraestructura universal de hooks, guardas de seguridad, reglas contextuales y adaptadores agnósticos diseñada para proteger los invariantes del proyecto **Enveda CASMI 2026 (Kaggle)** entre múltiples agentes de IA (**Google Antigravity**, **Claude Code**, **OpenAI Codex**) y desarrolladores humanos.

---

## 1. Tabla de Compatibilidad Verificada por Agente

| Agente de IA | Eventos Soportados Nativamente | Formato de Configuración | Garantía Nativa Interceptada | Cobertura de Respaldo (Git / CI) |
|---|---|---|---|---|
| **Claude Code** | `SessionStart`, `UserPromptSubmit`, `PreToolUse` (Write/Bash), `PostToolUse` (Write/Bash), `PreCompact`, `Stop`, `SubagentStop` | `.claude/settings.json` | Interceptación sincrónica total de llamadas y comandos con bloqueo `exit 2`. | Redundante con Git hooks (`pre-commit`, `pre-push`). |
| **OpenAI Codex** | `notify` (equivalente de `Stop`), directivas de sistema | `.codex/config.toml` + `AGENTS.md` | Notificación asíncrona de fin de turno y lectura de directivas. | **Hooks de Git (`G01–G06`)**, suite `run_checks.py pre-submit` y GitHub Actions CI. |
| **Google Antigravity** | `<user_rules>` automáticas, Skills (`.agents/skills/`), Workflows (`.agents/workflows/`) | `.agents/rules/*.md` + `.agents/workflows/*.md` | Inyección de invariantes en prompt de sistema y orquestación de subagentes. | **Hooks de Git locales (`core.hooksPath`)** + CI en GitHub Actions. |

---

## 2. Invariantes del Proyecto (`.agents/project.json`)

El archivo `.agents/project.json` es la **única fuente de verdad** de las constantes del desafío:
* **Métrica**: MRR@25 con canonicalización tautomérica **RDKit `2026.03.3`** + **InChIKey14**.
* **Presupuesto**: Máximo **9 horas** con margen de seguridad del **20%** ($\le 450$ min nominales).
* **Validación**: Partición por `molecule_id` (nunca por `spectrum_id`) con clustering MCES / Murcko para aislar `Val-Clase3` sobre $\ge 3$ semillas.
* **Preprocesamiento**: Umbral 1–2%, precursor $\pm 2.0$ Da, $\ge 5$ picos, masa neutra según aducto.
* **Seguridad**: Prohibido el acceso a internet en inferencia; bloqueo de archivos $> 25$ MB o pesos en Git.

---

## 3. Catálogo de Hooks Implementados

| Grupo | IDs | Descripción y Funcionalidad |
|---|---|---|
| **Contexto** | `H01`–`H03` | Contexto inicial de sesión (días restantes, RDKit, branch), inyector de prompts y volcado pre-compactación. |
| **Seguridad** | `H10`–`H14` | Bloqueo de secretos (`kaggle.json`, tokens), protección de `data/raw/`, bloqueo de binarios pesados en Git, comandos peligrosos (`push --force`, `rm -rf`) y salvaguarda offline. |
| **Dominio CASMI** | `H20`–`H30` | Anclaje RDKit 2026.03.3, golden test tautomérico, prevención de fuga en splits, cálculo exacto de MRR@25, validador de `submission.csv`, conversión masa-aducto, presupuesto de inferencia y registro de licencias comerciales. |
| **Calidad** | `H40`–`H43` | Formateo rápido (`ruff`), higiene de Jupyter Notebooks (< 2MB, sin outputs pesados), suite Pytest pre-push y chequeo de lockfiles. |
| **Trazabilidad** | `H50`–`H52` | Bitácora de experimentos en `EXPERIMENTS.md`, auditoría de envíos en `reports/submissions.csv` y sincronización de evidencias de `CHECKLIST.md`. |
| **Git Hooks** | `G01`–`G06` | Pre-commit rápido, validador de Conventional Commits (`commit-msg`), sugeridor de scopes, pre-push protector de `main` y post-commit activity log. |

---

## 4. Comandos de Verificación Rápida

```bash
# Ejecutar suite de pruebas de aceptación de todos los hooks (100% offline, stdlib)
python .agents/bin/selftest.py

# Verificaciones manuales
python .agents/bin/run_checks.py pre-commit   # Chequeo pre-commit
python .agents/bin/run_checks.py pre-push     # Chequeo pre-push y tests
python .agents/bin/run_checks.py pre-submit   # Auditoría completa pre-submission
```

---

## 5. Instrucciones para Protección de Rama `main` en GitHub

Para garantizar que nadie (humano o IA) pueda empujar directamente a `main` sin pasar por el CI y una revisión de código, ejecuta manualmente los siguientes pasos en la interfaz de GitHub (o vía CLI si posees permisos de administrador):

### Opción A: Interfaz Web de GitHub
1. Ve a **Settings** > **Branches** en tu repositorio `OctaLuna/enveda-casmi-2026`.
2. Haz clic en **Add branch protection rule**.
3. En **Branch name pattern**, escribe `main`.
4. Marca las siguientes casillas:
   - [x] **Require a pull request before merging** (Require approvals: 1).
   - [x] **Require status checks to pass before merging** (Selecciona el job `validate` de `ci.yml`).
   - [x] **Do not allow bypassing the above settings**.
5. Guarda los cambios.

### Opción B: GitHub CLI (`gh`)
*(Ejecutar únicamente desde tu terminal local si tienes privilegios de administrador)*:
```bash
gh api -X PUT repos/OctaLuna/enveda-casmi-2026/branches/main/protection \
  -H "Accept: application/vnd.github+json" \
  -F "required_status_checks[strict]=true" \
  -F "required_status_checks[contexts][]=validate" \
  -F "enforce_admins=true" \
  -F "required_pull_request_reviews[required_approving_review_count]=1" \
  -F "restrictions=null"
```

