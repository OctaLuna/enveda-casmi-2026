#!/usr/bin/env python3
"""
H12 - block-large-files
Bloquea el intento de agregar archivos mayores a large_file_mb (25 MB) o con extensiones
pesadas de datos/pesos (.parquet, .pt, .ckpt, .safetensors, .faiss, .index, etc.) a Git.
"""

from pathlib import Path
import re
import subprocess
import sys

HOOK_DIR = Path(__file__).resolve().parent.parent
LIB_DIR = HOOK_DIR / "lib"
if str(LIB_DIR) not in sys.path:
    sys.path.insert(0, str(LIB_DIR))

import common

FORBIDDEN_EXTENSIONS = {
    ".parquet", ".ckpt", ".pt", ".pth", ".safetensors",
    ".faiss", ".index", ".npy", ".npz", ".sdf"
}


def check_file(path_obj: Path, max_bytes: int) -> None:
    if not path_obj.exists():
        return

    ext = path_obj.suffix.lower()
    if ext in FORBIDDEN_EXTENSIONS:
        common.block(
            f"Archivo con extensión prohibida en Git: '{path_obj}' ({ext})",
            hook_id="H12",
            reason=f"Las extensiones binarias pesadas ({ext}) saturan el repositorio y rompen Git.",
            solution="Ignora el archivo en .gitignore y publícalo como un dataset en Kaggle Datasets o usa DVC / Git LFS."
        )

    if path_obj.is_file():
        size = path_obj.stat().st_size
        if size > max_bytes:
            size_mb = size / (1024 * 1024)
            common.block(
                f"Archivo demasiado grande para Git: '{path_obj}' ({size_mb:.2f} MB > {max_bytes / (1024 * 1024):.0f} MB)",
                hook_id="H12",
                reason="Git no debe contener archivos masivos; Kaggle no permite repos pesados ni GitHub permite blobs grandes.",
                solution="Carga los pesos o datasets como un Kaggle Dataset desacoplado y anota la ruta en kaggle/manifest.yaml."
            )


def check_git_staged_files(max_bytes: int) -> None:
    try:
        proc = subprocess.run(
            ["git", "diff", "--cached", "--name-only", "--diff-filter=ACM"],
            capture_output=True,
            text=True,
            check=False
        )
        if proc.returncode == 0:
            for line in proc.stdout.splitlines():
                f_path = Path(line.strip())
                check_file(f_path, max_bytes)
    except Exception as e:
        common.log_error("H12.git_check", f"Error inspeccionando staged files: {e}")


def main():
    payload = common.read_stdin_payload()
    config = common.load_project_config()
    max_mb = config.get("large_file_mb", 25)
    max_bytes = max_mb * 1024 * 1024

    event = payload.get("event", "")
    cmd = payload.get("command", "")

    # 1. Si es git pre-commit, comprobar staged
    if "pre_commit" in event or "git" in payload.get("agent", ""):
        check_git_staged_files(max_bytes)

    # 2. Si es comando bash que hace git add
    if cmd and "git add" in cmd:
        # Extraer posibles archivos de git add
        parts = cmd.split("git add", 1)[1].strip().split()
        for p in parts:
            if not p.startswith("-"):
                # Verificar extensiones o archivos
                for ext in FORBIDDEN_EXTENSIONS:
                    if p.lower().endswith(ext):
                        common.block(
                            f"Comando 'git add' incluye extensión bloqueada: '{p}'",
                            hook_id="H12",
                            reason="No se permite agregar archivos de datos o checkpoints a git.",
                            solution="Elimina el archivo del staging con 'git reset <archivo>' y agrégalo a .gitignore."
                        )
                f_path = Path(p)
                check_file(f_path, max_bytes)

    # 3. Archivos pasados explícitamente en paths
    for p in payload.get("paths", []):
        check_file(Path(p), max_bytes)

    sys.exit(0)


if __name__ == "__main__":
    main()
