#!/usr/bin/env python3
"""
H03 - pre-compact-save
Preserva el estado cognitivo de la sesión antes de una compactación de contexto (PreCompact).
Vuelca decisiones arquitectónicas, archivos modificados recientemente y tareas pendientes
en .agents/state/session-notes.md.
"""

from datetime import datetime
from pathlib import Path
import subprocess
import sys

HOOK_DIR = Path(__file__).resolve().parent.parent
LIB_DIR = HOOK_DIR / "lib"
if str(LIB_DIR) not in sys.path:
    sys.path.insert(0, str(LIB_DIR))

import common


def get_git_status() -> str:
    try:
        proc = subprocess.run(["git", "status", "--short"], capture_output=True, text=True, check=False)
        return proc.stdout.strip()
    except Exception:
        return "No disponible"


def main():
    payload = common.read_stdin_payload()
    config = common.load_project_config()
    root = common.find_project_root() or Path.cwd()
    state_dir = common.ensure_state_dir(root)
    notes_file = state_dir / "session-notes.md"

    now_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    git_stat = get_git_status()

    note_entry = f"""
## Resumen de Sesión Pre-Compactación ({now_str})
- **Agente**: {payload.get('agent', 'desconocido')}
- **Último Comando/Herramienta**: {payload.get('tool', 'n/a')} -> {payload.get('command', 'n/a')}
- **Archivos Modificados (Git Status)**:
```text
{git_stat}
```
---
"""
    try:
        with open(notes_file, "a", encoding="utf-8") as f:
            f.write(note_entry)
        common.log_activity(f"[{now_str}] Estado volcado a session-notes.md por H03")
    except Exception as e:
        common.log_error("H03.pre_compact_save", f"Error guardando notas: {e}")

    sys.exit(0)


if __name__ == "__main__":
    main()
