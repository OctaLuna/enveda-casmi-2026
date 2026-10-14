#!/usr/bin/env python3
"""
H11 - protect-raw-data
Bloquea cualquier intento de escribir, sobrescribir, mover o borrar archivos dentro
de protected_paths (data/raw/, train.parquet, etc.) o comandos destructivos como rm -rf data/.
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
    protected_paths = config.get("protected_paths", ["data/raw/", "data/external/"])

    # 1. Comandos destructivos en bash
    cmd = payload.get("command", "")
    if cmd:
        dangerous_patterns = [
            (r"(rm\s+-[rfRF]+|Remove-Item\s+-Recurse|del\s+/s)\s+.*?(data|models|train\.parquet|test\.parquet)",
             "Comando destructivo sobre directorios o archivos protegidos"),
            (r"(mv|move)\s+.*?(data/raw|train\.parquet)", "Intento de mover datos crudos originales"),
        ]
        for pat, desc in dangerous_patterns:
            if re.search(pat, cmd, re.IGNORECASE):
                common.block(
                    f"Comando bloqueado: {desc}",
                    hook_id="H11",
                    reason="Los datos crudos y modelos nunca deben eliminarse ni modificarse in situ (invariante CASMI).",
                    solution="Escribe transformaciones hacia data/processed/ o data/interim/ sin tocar data/raw/."
                )

    # 2. Rutas pasadas a herramientas de escritura/edición
    paths = payload.get("paths", [])
    for p in paths:
        norm_p = p.replace("\\", "/")
        for prot in protected_paths:
            norm_prot = prot.replace("\\", "/").rstrip("*")
            if norm_p.startswith(norm_prot) or f"/{norm_prot}" in norm_p:
                common.block(
                    f"Intento de modificar ruta protegida: '{p}'",
                    hook_id="H11",
                    reason="Los datos en data/raw/ son inmutables para garantizar reproducibilidad e integridad.",
                    solution="Guarda salidas limpias o particiones en 'data/processed/' o 'data/splits/'."
                )

        if "train.parquet" in norm_p and "raw" in norm_p:
            common.block(
                f"Intento de modificar '{p}'",
                hook_id="H11",
                reason="El archivo train.parquet original no debe ser sobrescrito.",
                solution="Usa data/processed/train_clean.parquet."
            )

    sys.exit(0)


if __name__ == "__main__":
    main()
