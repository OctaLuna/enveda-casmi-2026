#!/usr/bin/env python3
"""
H52 - checklist-sync
Audita el estado de CHECKLIST.md al finalizar una sesión comparando contra
las evidencias físicas existentes en el repositorio (.agents/checklist-evidence.yaml).
Reporta los elementos que ya disponen de artefactos tangibles generados.
Modo: warn.
"""

from pathlib import Path
import sys

HOOK_DIR = Path(__file__).resolve().parent.parent
LIB_DIR = HOOK_DIR / "lib"
if str(LIB_DIR) not in sys.path:
    sys.path.insert(0, str(LIB_DIR))

import common


def parse_simple_yaml_evidence(evidence_file: Path) -> list:
    items = []
    if not evidence_file.is_file():
        return items
    current = {}
    try:
        with open(evidence_file, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if line.startswith("- item:"):
                    if current:
                        items.append(current)
                    current = {"item": line.split(":", 1)[1].strip().strip("\"'")}
                elif ":" in line and current:
                    k, v = line.split(":", 1)
                    current[k.strip()] = v.strip().strip("\"'")
        if current:
            items.append(current)
    except Exception as e:
        common.log_error("H52.yaml", f"Error leyendo evidencias: {e}")
    return items


def main():
    payload = common.read_stdin_payload()
    config = common.load_project_config()
    root = common.find_project_root() or Path.cwd()

    evidence_file = root / ".agents" / "checklist-evidence.yaml"
    if not evidence_file.is_file():
        evidence_file = root / ".agent" / "checklist-evidence.yaml"

    evidences = parse_simple_yaml_evidence(evidence_file)
    if not evidences:
        sys.exit(0)

    completed_artifacts = []
    pending_artifacts = []

    for ev in evidences:
        expected_file = root / ev.get("file", "")
        desc = ev.get("pattern", ev.get("item", ""))
        if expected_file.is_file():
            completed_artifacts.append((desc, ev.get("file")))
        else:
            pending_artifacts.append((desc, ev.get("file")))

    print("\n--- Sincronización de Evidencias de Checklist (H52) ---")
    print(f"  * Artefactos Verificados en Disco: {len(completed_artifacts)}/{len(evidences)}")
    for desc, fpath in completed_artifacts:
        print(f"    [OK] {desc} -> {fpath}")
    if pending_artifacts:
        print("  * Artefactos Pendientes de Creación:")
        for desc, fpath in pending_artifacts[:3]:
            print(f"    [..] {desc} -> {fpath}")
    print("------------------------------------------------------\n")

    sys.exit(0)


if __name__ == "__main__":
    main()

