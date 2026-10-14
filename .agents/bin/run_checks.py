#!/usr/bin/env python3
"""
run-checks.py - Ejecución manual de suites de verificación para CASMI 2026.
Modos: pre-commit | pre-push | pre-submit
"""

import argparse
from pathlib import Path
import subprocess
import sys

BIN_DIR = Path(__file__).resolve().parent
AGENT_DIR = BIN_DIR.parent
DISPATCHER = BIN_DIR / "agent-hook"


def run_hook_event(event: str, agent: str = "git") -> int:
    cmd = [sys.executable, str(DISPATCHER), event, "--agent", agent]
    proc = subprocess.run(cmd)
    return proc.returncode


def main():
    parser = argparse.ArgumentParser(description="Ejecutar chequeos de hooks CASMI")
    parser.add_argument("mode", choices=["pre-commit", "pre-push", "pre-submit"], help="Modo de verificación")
    args = parser.parse_args()

    print(f"=== [CASMI Verificaciones Manuales: {args.mode}] ===")
    if args.mode == "pre-commit":
        rc = run_hook_event("git_pre_commit")
    elif args.mode == "pre-push":
        rc = run_hook_event("git_pre_push")
    elif args.mode == "pre-submit":
        rc = run_hook_event("pre_submit", agent="antigravity")

    if rc == 0:
        print(f"=== [OK] Todas las verificaciones de '{args.mode}' concluyeron exitosamente. ===")
        sys.exit(0)
    else:
        print(f"=== [FALLO] Las verificaciones de '{args.mode}' detectaron problemas (código {rc}). ===", file=sys.stderr)
        sys.exit(rc)


if __name__ == "__main__":
    main()
