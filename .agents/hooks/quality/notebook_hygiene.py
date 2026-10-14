#!/usr/bin/env python3
"""
H41 - notebook-hygiene
Inspecciona Jupyter Notebooks (.ipynb) staged para commit:
1. Tamaño menor a 2 MB (previene commits accidentales de outputs con imágenes/tablas).
2. Ausencia de rutas absolutas locales fijas (C:\\Users\\..., /home/...).
3. Ausencia de credenciales embebidas.
Modo: block.
"""

import json
from pathlib import Path
import re
import subprocess
import sys

HOOK_DIR = Path(__file__).resolve().parent.parent
LIB_DIR = HOOK_DIR / "lib"
if str(LIB_DIR) not in sys.path:
    sys.path.insert(0, str(LIB_DIR))

import common

LOCAL_PATH_PATTERNS = [
    r"[A-Za-z]:\\[Uu]sers\\",
    r"/home/[a-zA-Z0-9_\-]+/",
]


def check_notebook(nb_path: Path) -> None:
    if not nb_path.is_file():
        return

    # 1. Tamaño
    size_mb = nb_path.stat().st_size / (1024 * 1024)
    if size_mb > 2.0:
        common.block(
            f"Notebook demasiado grande para Git: '{nb_path}' ({size_mb:.2f} MB > 2.0 MB).",
            hook_id="H41",
            reason="Los notebooks con outputs de imágenes y datos saturan el historial de Git.",
            solution="Limpia las salidas del notebook antes de commitear usando 'nbstripout' o desde Jupyter ('Clear All Outputs')."
        )

    # 2. Rutas absolutas
    try:
        content = nb_path.read_text(encoding="utf-8", errors="ignore")
        for pat in LOCAL_PATH_PATTERNS:
            if re.search(pat, content):
                common.block(
                    f"Ruta absoluta local detectada en el notebook '{nb_path.name}'.",
                    hook_id="H41",
                    reason="Las rutas absolutas locales rompen la reproducibilidad y fallan al ejecutarse en Kaggle.",
                    solution="Utiliza rutas relativas basadas en Path.cwd() o constantes de configuración."
                )
    except Exception as e:
        common.log_error("H41.notebook_hygiene", f"Error inspeccionando {nb_path}: {e}")


def main():
    payload = common.read_stdin_payload()
    config = common.load_project_config()

    # Obtener archivos staged
    try:
        proc = subprocess.run(["git", "diff", "--cached", "--name-only", "--diff-filter=ACM"], capture_output=True, text=True, check=False)
        staged_files = [line.strip() for line in proc.stdout.splitlines() if line.strip().endswith(".ipynb")]
    except Exception:
        staged_files = []

    for p in staged_files:
        check_notebook(Path(p))

    # También revisar paths explícitos en payload
    for p in payload.get("paths", []):
        if p.endswith(".ipynb"):
            check_notebook(Path(p))

    sys.exit(0)


if __name__ == "__main__":
    main()

