#!/usr/bin/env python3
"""
H14 - offline-guard
Protege los módulos y notebooks de inferencia contra llamadas a internet (invariante Kaggle offline).
Detecta imports y llamadas de red como requests, urllib, wget, gdown, git clone,
huggingface_hub downloads y from_pretrained remotos en rutas de inferencia.
"""

from pathlib import Path
import re
import sys

HOOK_DIR = Path(__file__).resolve().parent.parent
LIB_DIR = HOOK_DIR / "lib"
if str(LIB_DIR) not in sys.path:
    sys.path.insert(0, str(LIB_DIR))

import common

NETWORK_PATTERNS = [
    (r"\bimport\s+requests\b|\bfrom\s+requests\b|\brequests\.(get|post|put|delete)\b", "Llamada HTTP con 'requests'"),
    (r"\burllib\.request\b|\burllib3\b", "Llamada HTTP con 'urllib'"),
    (r"\bwget\b|\bgdown\b", "Descargador de archivos wget/gdown"),
    (r"\bgit\s+clone\b", "Comando de clonación git"),
    (r"\bhf_hub_download\b|\bsnapshot_download\b", "Descarga remota de HuggingFace"),
    (r"\.from_pretrained\s*\(\s*['\"][a-zA-Z0-9_\-]+/[a-zA-Z0-9_\-]+['\"]", "Carga remota from_pretrained con repo HuggingFace"),
    (r"\bpip\s+install\b", "Llamada a pip install durante inferencia"),
]


def check_content(content: str, source_desc: str) -> None:
    for regex, desc in NETWORK_PATTERNS:
        match = re.search(regex, content, re.IGNORECASE)
        if match:
            common.block(
                f"Llamada a red prohibida en código de inferencia: {desc} -> '{match.group(0)}' en {source_desc}",
                hook_id="H14",
                reason="La evaluación de Kaggle corre estrictamente sin acceso a internet; llamadas a red causarán fallo fatal.",
                solution="Carga los pesos y artefactos exclusivamente desde rutas locales (/kaggle/input/... o models/) empaquetadas en datasets."
            )


def main():
    payload = common.read_stdin_payload()
    config = common.load_project_config()
    offline_paths = config.get("offline_paths", ["inference/", "notebooks/final/", "src/inference/", "src/api/"])

    paths = payload.get("paths", [])
    content = payload.get("content", "")

    for p in paths:
        norm_p = p.replace("\\", "/")
        is_offline_path = any(norm_p.startswith(op.rstrip("*")) or op in norm_p for op in offline_paths)
        if is_offline_path:
            # Comprobar contenido directo del payload
            if content:
                check_content(content, f"payload para '{p}'")
            # Comprobar contenido del archivo si existe
            p_obj = Path(p)
            if p_obj.is_file():
                try:
                    with open(p_obj, "r", encoding="utf-8", errors="ignore") as f:
                        check_content(f.read(), f"archivo '{p}'")
                except Exception:
                    pass

    sys.exit(0)


if __name__ == "__main__":
    main()
