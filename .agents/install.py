#!/usr/bin/env python3
"""
install.py - Instalador idempotente del sistema de hooks multi-agente CASMI 2026.
Soporta:
  --local  (por defecto) : Activa core.hooksPath, genera configs de Claude/Codex y crea .agents/state/
  --global                : Enlaza utilidades a nivel de usuario sin sobrescribir destructivamente
  --check                 : Audita el estado actual de la instalación sin alterar nada
"""

import argparse
from pathlib import Path
import shutil
import subprocess
import sys


def find_repo_root() -> Path:
    current = Path(__file__).resolve().parent
    for p in [current] + list(current.parents):
        if (p / ".git").is_dir() or (p / ".agents").is_dir():
            return p
    return Path.cwd()


def run_cmd(cmd: list) -> tuple:
    try:
        proc = subprocess.run(cmd, capture_output=True, text=True, check=False)
        return proc.returncode, proc.stdout.strip(), proc.stderr.strip()
    except Exception as e:
        return 1, "", str(e)


def install_local(root: Path) -> None:
    print("=== [Instalación Local de Hooks CASMI 2026] ===")

    # 1. Crear directorio de estado
    state_dir = root / ".agents" / "state"
    state_dir.mkdir(parents=True, exist_ok=True)
    print(f" [OK] Directorio de estado verificado: {state_dir}")

    # 2. Configurar Git core.hooksPath
    git_hooks_dir = root / ".agents" / "git-hooks"
    if git_hooks_dir.is_dir():
        rc, out, err = run_cmd(["git", "config", "core.hooksPath", ".agents/git-hooks"])
        if rc == 0:
            print(" [OK] Git core.hooksPath configurado a '.agents/git-hooks'.")
        else:
            print(f" [WARN] No se pudo configurar git core.hooksPath: {err}")

    # 3. Generar .claude/settings.json desde plantilla
    claude_tmpl = root / ".agents" / "adapters" / "claude" / "settings.template.json"
    claude_target = root / ".claude" / "settings.json"
    if claude_tmpl.is_file():
        claude_target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(claude_tmpl, claude_target)
        print(" [OK] Configuración de Claude Code generada en .claude/settings.json")

    # 4. Generar .codex/config.toml desde plantilla
    codex_tmpl = root / ".agents" / "adapters" / "codex" / "config.template.toml"
    codex_target = root / ".codex" / "config.toml"
    if codex_tmpl.is_file():
        codex_target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(codex_tmpl, codex_target)
        print(" [OK] Configuración de Codex generada en .codex/config.toml")

    print("=== Instalación local completada exitosamente. ===")


def check_status(root: Path) -> None:
    print("=== [Auditoría del Sistema de Hooks CASMI] ===")

    # 1. Git hooks
    rc, out, _ = run_cmd(["git", "config", "core.hooksPath"])
    hooks_path = out if rc == 0 else "no configurado"
    print(f" * Git core.hooksPath:          {hooks_path}")

    # 2. Adaptador Claude
    claude_cfg = root / ".claude" / "settings.json"
    print(f" * Claude Code (.claude):       {'Instalado' if claude_cfg.is_file() else 'No configurado'}")

    # 3. Adaptador Codex
    codex_cfg = root / ".codex" / "config.toml"
    print(f" * Codex CLI (.codex):          {'Instalado' if codex_cfg.is_file() else 'No configurado'}")

    # 4. Project.json
    proj_cfg = root / ".agents" / "project.json"
    print(f" * Configuración project.json:  {'Presente' if proj_cfg.is_file() else 'Faltante'}")

    # 5. Directorio state
    state_dir = root / ".agents" / "state"
    print(f" * Directorio de estado:        {'Activo' if state_dir.is_dir() else 'Pendiente'}")
    print("===============================================")


def install_global(root: Path) -> None:
    print("=== [Instalación Global (No Destructiva)] ===")
    user_home = Path.home()
    target_dir = user_home / ".agents"
    print(f"Directorio de usuario objetivo: {target_dir}")
    if target_dir.exists():
        print("Directorio global ~/.agents ya existe. No se sobrescribirá.")
    else:
        try:
            target_dir.mkdir(parents=True, exist_ok=True)
            print("Directorio global ~/.agents creado.")
        except Exception as e:
            print(f"Error creando ~/.agents: {e}")
    print("Para activar hooks globales en otros repositorios, ejecuta:")
    print("  git config --global core.hooksPath ~/.agents/git-hooks")


def main():
    parser = argparse.ArgumentParser(description="Instalador de Hooks CASMI 2026")
    parser.add_argument("--local", action="store_true", default=False, help="Instalación local en el repositorio")
    parser.add_argument("--global", dest="is_global", action="store_true", default=False, help="Configuración opcional a nivel de usuario")
    parser.add_argument("--check", action="store_true", default=False, help="Auditar estado actual de la instalación")

    args = parser.parse_args()
    root = find_repo_root()

    if args.check:
        check_status(root)
    elif args.is_global:
        install_global(root)
    else:
        install_local(root)


if __name__ == "__main__":
    main()

