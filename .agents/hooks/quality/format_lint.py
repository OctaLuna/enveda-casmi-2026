#!/usr/bin/env python3
"""
H40 - format-lint
Aplica ruff format y ruff check --fix exclusivamente sobre el archivo Python
que acaba de ser editado por el agente.
Si ruff no está instalado, continúa en silencio sin bloquear.
Modo: warn.
"""

from pathlib import Path
import subprocess
import sys

HOOK_DIR = Path(__file__).resolve().parent.parent
LIB_DIR = HOOK_DIR / "lib"
if str(LIB_DIR) not in sys.path:
    sys.path.insert(0, str(LIB_DIR))

import common


def run_ruff_on_file(file_path: Path) -> None:
    if not file_path.is_file() or file_path.suffix != ".py":
        return
    try:
        # Formatear
        subprocess.run(["ruff", "format", str(file_path)], capture_output=True, check=False)
        # Corregir lints seguros
        subprocess.run(["ruff", "check", "--fix", str(file_path)], capture_output=True, check=False)
    except FileNotFoundError:
        # Ruff no está en PATH
        pass
    except Exception as e:
        common.log_error("H40.format_lint", f"Error ejecutando ruff en {file_path}: {e}")


def main():
    payload = common.read_stdin_payload()
    config = common.load_project_config()

    paths = payload.get("paths", [])
    for p in paths:
        path_obj = Path(p)
        if path_obj.suffix == ".py":
            run_ruff_on_file(path_obj)

    sys.exit(0)


if __name__ == "__main__":
    main()

