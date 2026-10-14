#!/usr/bin/env python3
"""
H28 - packaging-manifest-check
Verifica que kaggle/manifest.yaml liste cada checkpoint de modelo o peso
utilizado durante inferencia (DreaMS, MIST, DiffMS, Ensamble) con su slug de Kaggle Dataset,
versión, sha256 y licencia comercial válida.
"""

from pathlib import Path
import sys

HOOK_DIR = Path(__file__).resolve().parent.parent
LIB_DIR = HOOK_DIR / "lib"
if str(LIB_DIR) not in sys.path:
    sys.path.insert(0, str(LIB_DIR))

import common


def parse_manifest_entries(manifest_path: Path) -> list:
    entries = []
    if not manifest_path.is_file():
        return entries
    current_entry = {}
    with open(manifest_path, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith("#"):
                continue
            if line.startswith("- "):
                if current_entry:
                    entries.append(current_entry)
                current_entry = {}
                line = line[2:].strip()
            if ":" in line:
                k, v = line.split(":", 1)
                current_entry[k.strip()] = v.strip().strip("\"'")
    if current_entry:
        entries.append(current_entry)
    return entries


def main():
    payload = common.read_stdin_payload()
    config = common.load_project_config()
    root = common.find_project_root() or Path.cwd()

    manifest_file = root / "kaggle" / "manifest.yaml"
    if not manifest_file.is_file():
        # Si no existe manifest, solo advertir a menos que estemos en pre_submit
        if "pre_submit" in payload.get("event", ""):
            common.block(
                "Falta el archivo kaggle/manifest.yaml requerido para el empaquetado de submission.",
                hook_id="H28",
                reason="Todos los modelos de inferencia deben estar formalmente catalogados con su origen y sha256.",
                solution="Crea kaggle/manifest.yaml listando datasets, pesos y hashes."
            )
        else:
            common.warn("kaggle/manifest.yaml aún no ha sido creado. Recuerda generarlo antes del release.", hook_id="H28")
            sys.exit(0)

    entries = parse_manifest_entries(manifest_file)
    required_fields = {"dataset_slug", "version", "sha256", "license"}
    for idx, entry in enumerate(entries, start=1):
        missing = required_fields - set(entry.keys())
        if missing:
            common.block(
                f"Entrada #{idx} en kaggle/manifest.yaml carece de campos obligatorios: {missing}",
                hook_id="H28",
                reason="El manifiesto debe garantizar trazabilidad y reproducibilidad de los pesos.",
                solution=f"Asegura que cada entrada incluya {required_fields}."
            )

    sys.exit(0)


if __name__ == "__main__":
    main()
