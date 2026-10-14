#!/usr/bin/env python3
"""
H10 - block-secrets
Detecta credenciales sensibles (Kaggle API keys, GitHub tokens, AWS/GCP keys, .env)
tanto en archivos modificados como en comandos de consola (ej. cat ~/.kaggle/kaggle.json).
"""

from pathlib import Path
import re
import sys

HOOK_DIR = Path(__file__).resolve().parent.parent
LIB_DIR = HOOK_DIR / "lib"
if str(LIB_DIR) not in sys.path:
    sys.path.insert(0, str(LIB_DIR))

import common

PATTERNS = [
    (r"KAGGLE_KEY\s*=\s*['\"][a-zA-Z0-9]{10,}['\"]", "Credencial KAGGLE_KEY expuesta"),
    (r"KAGGLE_USERNAME\s*=\s*['\"][a-zA-Z0-9_\-]{3,}['\"]", "Usuario KAGGLE_USERNAME con valor asignado"),
    (r"\"key\"\s*:\s*\"[a-zA-Z0-9]{10,}\"", "Clave en formato kaggle.json"),
    (r"ghp_[a-zA-Z0-9]{20,}", "Token de acceso personal de GitHub (ghp_)"),
    (r"github_pat_[a-zA-Z0-9_]{22,}", "Token de GitHub fine-grained"),
    (r"AKIA[0-9A-Z]{16}", "AWS Access Key ID"),
    (r"AIza[0-9A-Za-z\-_]{35}", "Google API Key"),
    (r"(cat|type|more|less|head|tail|Get-Content)\s+.*?(\.kaggle[\\/]kaggle\.json|kaggle\.json)", "Comando para exponer archivo kaggle.json"),
]


def check_text(text: str, context: str) -> None:
    for regex, desc in PATTERNS:
        if re.search(regex, text, re.IGNORECASE):
            common.block(
                f"Se detectó un secreto o credencial no autorizada en {context}: {desc}",
                hook_id="H10",
                reason="Prevenir la filtración de credenciales de Kaggle, tokens de Git o claves cloud al repositorio o contexto.",
                solution="Usa variables de entorno seguras, elimina el token del archivo o evita imprimir credenciales."
            )


def main():
    payload = common.read_stdin_payload()
    config = common.load_project_config()

    # 1. Chequeo de comando
    cmd = payload.get("command", "")
    if cmd:
        check_text(cmd, "comando a ejecutar")

    # 2. Chequeo de contenido en payload
    content = payload.get("content", "")
    if content:
        check_text(content, "contenido de la herramienta")

    # 3. Chequeo de archivos objetivo
    paths = payload.get("paths", [])
    for p in paths:
        path_obj = Path(p)
        if path_obj.name.lower() in ("kaggle.json", ".env"):
            common.block(
                f"Intento de modificar o commitear archivo sensible: {path_obj.name}",
                hook_id="H10",
                reason="Los archivos kaggle.json y .env están estrictamente prohibidos en el repo.",
                solution="Agrega el archivo a .gitignore y usa Kaggle Secrets."
            )
        if path_obj.is_file():
            try:
                # Si es menor a 2MB leer y comprobar
                if path_obj.stat().st_size < 2 * 1024 * 1024:
                    with open(path_obj, "r", encoding="utf-8", errors="ignore") as f:
                        check_text(f.read(), f"archivo {path_obj.name}")
            except Exception:
                pass

    sys.exit(0)


if __name__ == "__main__":
    main()
