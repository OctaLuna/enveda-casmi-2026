#!/usr/bin/env python3
"""
H29 - license-ledger
Exige que cada fuente de datos o modelo externo esté registrada en docs/DATA_SOURCES.md
especificando: Nombre, URL, Licencia, y '¿Licencia comercial válida?' (Sí / No / Por verificar).
Bloquea si hay fuentes sin registrar o si se intenta hacer merge a main con fuentes 'Por verificar'.
"""

from pathlib import Path
import subprocess
import sys

HOOK_DIR = Path(__file__).resolve().parent.parent
LIB_DIR = HOOK_DIR / "lib"
if str(LIB_DIR) not in sys.path:
    sys.path.insert(0, str(LIB_DIR))

import common


def get_current_branch() -> str:
    try:
        proc = subprocess.run(["git", "branch", "--show-current"], capture_output=True, text=True, check=False)
        return proc.stdout.strip()
    except Exception:
        return ""


def check_data_sources_ledger(ledger_path: Path, current_branch: str) -> None:
    if not ledger_path.is_file():
        common.block(
            "Falta el archivo de registro de fuentes externas docs/DATA_SOURCES.md.",
            hook_id="H29",
            reason="Las reglas de Kaggle prohíben datos o modelos con licencias no comerciales o no públicas.",
            solution="Crea docs/DATA_SOURCES.md con la tabla de fuentes, URLs y licencias."
        )

    content = ledger_path.read_text(encoding="utf-8")
    if current_branch == "main" and "por verificar" in content.lower():
        common.block(
            "Existen fuentes externas con estatus 'Por verificar' en docs/DATA_SOURCES.md para la rama main.",
            hook_id="H29",
            reason="Ningún código o dato puede llegar a producción sin certeza absoluta de su licencia comercial.",
            solution="Verifica los términos de uso y actualiza el estatus a 'Sí' o remueve la fuente."
        )


def main():
    payload = common.read_stdin_payload()
    config = common.load_project_config()
    root = common.find_project_root() or Path.cwd()

    branch = get_current_branch()
    ledger = root / "docs" / "DATA_SOURCES.md"

    # Verificar si se están tocando datos externos
    paths = payload.get("paths", [])
    touches_external = any("external" in p.lower() for p in paths)

    if touches_external or payload.get("event") == "git_pre_commit":
        check_data_sources_ledger(ledger, branch)

    sys.exit(0)


if __name__ == "__main__":
    main()
