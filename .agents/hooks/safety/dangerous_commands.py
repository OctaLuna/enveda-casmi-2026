#!/usr/bin/env python3
"""
H13 - dangerous-commands
Bloquea comandos destructivos o peligrosos en Bash:
- git push --force / -f
- git reset --hard
- rm -rf / o ~
- curl ... | sh
- gh pr merge sin checks verdes
- pip install fuera de lockfile (warn)
"""

from pathlib import Path
import re
import subprocess
import sys

HOOK_DIR = Path(__file__).resolve().parent.parent
LIB_DIR = HOOK_DIR / "lib"
if str(LIB_DIR) not in sys.path:
    sys.path.insert(0, str(LIB_DIR))

import common

DANGEROUS_BLOCK_PATTERNS = [
    (r"git\s+push\s+.*(--force|-f\b)", "git push forzado prohibido"),
    (r"git\s+reset\s+--hard", "git reset --hard no permitido directamente desde agente"),
    (r"rm\s+-[rfRF]+\s+([/~]|\$HOME)", "rm destructivo sobre la raíz o directorio de usuario"),
    (r"(curl|wget)\s+.*?\|\s*(sh|bash|powershell|pwsh)", "Pipe inseguro de red hacia shell"),
]


def check_gh_pr_merge(cmd: str) -> None:
    if "gh pr merge" in cmd:
        try:
            # Ejecutar gh pr checks
            proc = subprocess.run(["gh", "pr", "checks"], capture_output=True, text=True, check=False)
            if proc.returncode != 0 or "fail" in proc.stdout.lower() or "pending" in proc.stdout.lower():
                common.block(
                    "No se puede fusionar el Pull Request: checks de CI fallidos o pendientes.",
                    hook_id="H13",
                    reason="La política de integración exige que todos los tests y linters pasen antes del merge.",
                    solution="Espera a que pasen los checks en GitHub o resuelve los errores señalados."
                )
        except FileNotFoundError:
            common.warn("Herramienta 'gh' no encontrada en PATH para verificar checks de PR.", hook_id="H13")


def main():
    payload = common.read_stdin_payload()
    config = common.load_project_config()
    cmd = payload.get("command", "")
    if not cmd:
        sys.exit(0)

    for pat, desc in DANGEROUS_BLOCK_PATTERNS:
        if re.search(pat, cmd, re.IGNORECASE):
            common.block(
                f"Comando peligroso detectado: {desc} -> '{cmd}'",
                hook_id="H13",
                reason="Protección estricta contra pérdida de historial de Git y seguridad del sistema operativo.",
                solution="Usa flujos estándar de Git (PRs, commits de corrección) sin forzar sobrescritura."
            )

    # Guarda gh pr merge
    check_gh_pr_merge(cmd)

    # Advertencia sobre pip install fuera de entorno fijado
    if re.search(r"pip\s+install\s+", cmd, re.IGNORECASE) and "-r" not in cmd and "requirements" not in cmd:
        common.warn(
            f"Se detectó instalación manual con pip: '{cmd}'. Recuerda fijar cualquier dependencia en requirements.txt.",
            hook_id="H13"
        )

    sys.exit(0)


if __name__ == "__main__":
    main()
