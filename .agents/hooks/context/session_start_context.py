#!/usr/bin/env python3
"""
H01 - session-start-context
Inyecta contexto vital al inicio de cada sesión de agente:
- Días restantes hasta el cierre de equipos (7-dic-2026) y deadline final (14-dic-2026)
- Rama Git activa
- Última entrada de experimentos (EXPERIMENTS.md)
- Resumen de ítems pendientes en CHECKLIST.md
- Estado de versión de RDKit
"""

from datetime import datetime, timezone
from pathlib import Path
import subprocess
import sys

HOOK_DIR = Path(__file__).resolve().parent.parent
LIB_DIR = HOOK_DIR / "lib"
if str(LIB_DIR) not in sys.path:
    sys.path.insert(0, str(LIB_DIR))

import common


def get_git_info() -> str:
    try:
        proc = subprocess.run(["git", "branch", "--show-current"], capture_output=True, text=True, check=False)
        return proc.stdout.strip() or "HEAD detached"
    except Exception:
        return "desconocida"


def get_days_remaining(target_iso: str) -> int:
    try:
        target = datetime.fromisoformat(target_iso.replace("Z", "+00:00"))
        now = datetime.now(timezone.utc)
        return max(0, (target - now).days)
    except Exception:
        return -1


def get_last_experiment(root: Path) -> str:
    exp_file = root / "EXPERIMENTS.md"
    if not exp_file.is_file():
        return "Ninguno registrado aún"
    try:
        lines = exp_file.read_text(encoding="utf-8").splitlines()
        for line in reversed(lines):
            if line.strip().startswith("|") and not line.strip().startswith("| Fecha") and not line.strip().startswith("|---"):
                return line.strip()
    except Exception:
        pass
    return "Sin entradas tabulares"


def count_checklist(root: Path) -> tuple:
    chk_file = root / "CHECKLIST.md"
    if not chk_file.is_file():
        return (0, 0)
    try:
        content = chk_file.read_text(encoding="utf-8")
        total = content.count("- [ ]") + content.count("- [x]")
        done = content.count("- [x]")
        return (done, total)
    except Exception:
        return (0, 0)


def get_rdkit_status(expected: str) -> str:
    try:
        import rdkit
        v = getattr(rdkit, "__version__", "desconocida")
        return f"{v} (OK)" if v == expected else f"{v} (ALERTA: esperado {expected})"
    except ImportError:
        return f"No instalado en intérprete (fijado {expected} en requirements.txt)"


def main():
    payload = common.read_stdin_payload()
    config = common.load_project_config()
    root = common.find_project_root() or Path.cwd()

    dates = config.get("dates", {})
    days_team = get_days_remaining(dates.get("team_deadline", "2026-12-07T23:59:00Z"))
    days_final = get_days_remaining(dates.get("final_deadline_utc", "2026-12-14T23:59:00Z"))

    branch = get_git_info()
    last_exp = get_last_experiment(root)
    done_chk, total_chk = count_checklist(root)
    rdkit_stat = get_rdkit_status(config.get("rdkit_version", "2026.03.3"))

    print("\n========================================================")
    print("      ENVEDA CASMI 2026 - CONTEXTO OPERATIVO INICIAL   ")
    print("========================================================")
    print(f" * Días para Cierre Equipos (7-Dic):   {days_team} días")
    print(f" * Días para Deadline Final (14-Dic):  {days_final} días")
    print(f" * Rama Git Activa:                    {branch}")
    print(f" * Versión RDKit:                      {rdkit_stat}")
    print(f" * Checklist de Ejecución:             {done_chk}/{total_chk} tareas completadas")
    print(f" * Último Experimento:                 {last_exp[:80]}")
    print("========================================================\n")

    sys.exit(0)


if __name__ == "__main__":
    main()

