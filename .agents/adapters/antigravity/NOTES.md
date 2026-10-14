# Notas de Compatibilidad y Adaptador para Google Antigravity
**Path**: `.agents/adapters/antigravity/NOTES.md`

## 1. Arquitectura de Soporte en Antigravity
* **Reglas Persistentes de Contexto**: Antigravity carga reglas desde `.agents/rules/` y las inyecta en el prompt del sistema (`<user_rules>`).
* **Workflows y Slash Commands**: Se definen en `.agents/workflows/` (`/pre-submit`, `/new-experiment`, `/pre-pr`).
* **Habilidades Modulares (Skills)**: Colección de 15 skills del proyecto alojadas en `.agents/skills/`.

## 2. Garantías de Ejecución
* **Hooks Nativos de Ciclo de Vida**: Antigravity no expone un bus nativo de interceptación sincrónica de llamadas a herramientas tipo `PreToolUse` por stdin.
* **Mecanismos de Respaldo Reforzados**:
  1. Reglas imperativas activas en el contexto (`casmi-invariantes.md`, `datos-protegidos.md`, `offline-inference.md`).
  2. Invocación manual o automatizada de workflows vía slash command o terminal (`python .agents/bin/run_checks.py`).
  3. **Red de Seguridad Infranqueable**: Hooks de Git locales (`.agents/git-hooks/pre-commit`, `pre-push`, `commit-msg`) configurados mediante `core.hooksPath`. Ningún cambio puede ser commiteado ni empujado a Git sin pasar las validaciones.
  4. **GitHub Actions CI**: Pipeline en `.github/workflows/ci.yml` ejecutando `selftest.py`, pytest y linters.
