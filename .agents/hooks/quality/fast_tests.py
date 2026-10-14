#!/usr/bin/env python3
"""
H42 - fast-tests
Ejecuta la suite de pruebas unitarias rápidas de Pytest (pytest -m "not slow" o pytest tests/ -v)
antes de autorizar envíos de código a Git remoto o empaquetado final de submission.
Modo: block.
"""

from pathlib import Path
import subprocess
import sys

HOOK_DIR = Path(__file__).resolve().parent.parent
LIB_DIR = HOOK_DIR / "lib"
if str(LIB_DIR) not in sys.path:
    sys.path.insert(0, str(LIB_DIR))

import common


def run_tests(root: Path) -> None:
    tests_dir = root / "tests"
    if not tests_dir.is_dir():
        return

    print("=== [H42: Ejecutando Suite de Tests Rápidos] ===")
    try:
        # Intentar pytest -m "not slow"
        cmd = [sys.executable, "-m", "pytest", "tests/", "-m", "not slow", "-v"]
        proc = subprocess.run(cmd, cwd=str(root))
        if proc.returncode != 0:
            # Reintentar pytest tests/ directo si el marcador not slow no está configurado
            cmd_fallback = [sys.executable, "-m", "pytest", "tests/", "-v"]
            proc_fallback = subprocess.run(cmd_fallback, cwd=str(root))
            if proc_fallback.returncode != 0:
                common.block(
                    "La suite de pruebas automatizadas falló.",
                    hook_id="H42",
                    reason="No se permite enviar código ni generar releases con pruebas en rojo.",
                    solution="Ejecuta 'pytest tests/ -v' localmente y corrige los fallos detectados."
                )
    except FileNotFoundError:
        common.warn("Pytest no se encuentra disponible en este entorno; omitiendo suite de pruebas.", hook_id="H42")
    except Exception as e:
        common.log_error("H42.fast_tests", f"Excepción ejecutando pytest: {e}")


def main():
    payload = common.read_stdin_payload()
    config = common.load_project_config()
    root = common.find_project_root() or Path.cwd()

    run_tests(root)
    sys.exit(0)


if __name__ == "__main__":
    main()

