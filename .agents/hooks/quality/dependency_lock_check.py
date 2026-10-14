#!/usr/bin/env python3
"""
H43 - dependency-lock-check
Avisa cuando se modifican archivos de dependencias (requirements.txt, pyproject.toml, environment.yml)
recordando regenerar el lockfile correspondiente y verificando que rdkit permanezca fijado.
Modo: warn.
"""

from pathlib import Path
import re
import sys

HOOK_DIR = Path(__file__).resolve().parent.parent
LIB_DIR = HOOK_DIR / "lib"
if str(LIB_DIR) not in sys.path:
    sys.path.insert(0, str(LIB_DIR))

import common


def main():
    payload = common.read_stdin_payload()
    config = common.load_project_config()
    expected_rdkit = config.get("rdkit_version", "2026.03.3")

    paths = payload.get("paths", [])
    for p in paths:
        path_obj = Path(p)
        if any(path_obj.name.startswith(pre) for pre in ["requirements", "environment", "pyproject"]):
            common.warn(
                f"Se modificó '{path_obj.name}'. Recuerda regenerar el lockfile o actualizar el entorno de los otros desarrolladores.",
                hook_id="H43"
            )
            try:
                content = path_obj.read_text(encoding="utf-8")
                if "rdkit" in content.lower() and f"rdkit=={expected_rdkit}" not in content:
                    common.warn(
                        f"¡Alerta! RDKit no parece estar fijado exactamente a 'rdkit=={expected_rdkit}' en {path_obj.name}.",
                        hook_id="H43"
                    )
            except Exception:
                pass

    sys.exit(0)


if __name__ == "__main__":
    main()

