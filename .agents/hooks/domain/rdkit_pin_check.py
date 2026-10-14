#!/usr/bin/env python3
"""
H20 - rdkit-pin-check
Verifica que la versión de RDKit esté estrictamente anclada a 2026.03.3.
Un desajuste en RDKit altera la canonicalización de tautómeros y rompe la correlación
entre el MRR@25 local y el marcador de Kaggle.
"""

from pathlib import Path
import re
import sys

HOOK_DIR = Path(__file__).resolve().parent.parent
LIB_DIR = HOOK_DIR / "lib"
if str(LIB_DIR) not in sys.path:
    sys.path.insert(0, str(LIB_DIR))

import common


def check_lockfiles(expected_ver: str, project_root: Path) -> None:
    files_to_check = [
        project_root / "requirements.txt",
        project_root / "requirements.lock",
        project_root / "environment.yml"
    ]
    found_rdkit = False
    for req_file in files_to_check:
        if req_file.is_file():
            try:
                content = req_file.read_text(encoding="utf-8")
                # Buscar rdkit
                matches = re.findall(r"rdkit([=~><!]=?)([0-9a-zA-Z\.\-]+)", content, re.IGNORECASE)
                if matches:
                    found_rdkit = True
                    for op, ver in matches:
                        if op != "==" or ver.strip() != expected_ver:
                            common.block(
                                f"RDKit no está fijado exactamente a {expected_ver} en {req_file.name}: 'rdkit{op}{ver}'",
                                hook_id="H20",
                                reason="Kaggle evalúa tautómeros con RDKit 2026.03.3; cualquier otra versión altera los InChIKey14.",
                                solution=f"Fija 'rdkit=={expected_ver}' en {req_file.name}."
                            )
            except Exception:
                pass


def check_runtime_version(expected_ver: str) -> None:
    try:
        import rdkit
        runtime_ver = getattr(rdkit, "__version__", "")
        if runtime_ver and runtime_ver != expected_ver:
            common.block(
                f"Versión de RDKit activa ({runtime_ver}) no coincide con la esperada ({expected_ver}).",
                hook_id="H20",
                reason="Divergencia entre entorno local y runtime de evaluación de Kaggle.",
                solution=f"Ejecuta 'pip install rdkit=={expected_ver}' en tu entorno virtual."
            )
    except ImportError:
        # Si no está instalado en este intérprete, advertir
        common.warn(f"RDKit no está instalado en el intérprete de ejecución actual ({sys.executable}).", hook_id="H20")


def main():
    payload = common.read_stdin_payload()
    config = common.load_project_config()
    expected_ver = config.get("rdkit_version", "2026.03.3")

    root = common.find_project_root() or Path.cwd()
    check_lockfiles(expected_ver, root)
    check_runtime_version(expected_ver)

    sys.exit(0)


if __name__ == "__main__":
    main()
