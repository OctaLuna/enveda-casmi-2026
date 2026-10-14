#!/usr/bin/env python3
"""
H24 - submission-validator
Valida rigurosamente el formato de submission.csv para Kaggle:
- Encabezados requeridos (molecule_id, smiles)
- Máximo max_candidates (25) candidatos por molécula
- Separador ';'
- Sin valores vacíos, nulos o NaN
- Sin duplicados en la misma fila
"""

import csv
from pathlib import Path
import sys

HOOK_DIR = Path(__file__).resolve().parent.parent
LIB_DIR = HOOK_DIR / "lib"
if str(LIB_DIR) not in sys.path:
    sys.path.insert(0, str(LIB_DIR))

import common


def validate_file(sub_path: Path, max_candidates: int, sep: str) -> None:
    if not sub_path.is_file():
        return

    with open(sub_path, "r", encoding="utf-8") as f:
        reader = csv.reader(f)
        header = next(reader, None)
        if not header:
            common.block(f"Archivo de submission vacío: {sub_path.name}", hook_id="H24")

        norm_header = [h.strip().lower() for h in header]
        if "molecule_id" not in norm_header:
            common.block(
                f"Falta columna obligatoria 'molecule_id' en {sub_path.name}. Cabecera: {header}",
                hook_id="H24",
                reason="El evaluador de Kaggle requiere la columna de identificación de molécula.",
                solution="Verifica los nombres de columna en sample_submission.csv."
            )

        smiles_idx = -1
        for idx, col in enumerate(norm_header):
            if col in ("smiles", "prediction", "candidates"):
                smiles_idx = idx
                break

        if smiles_idx == -1:
            common.block(
                f"No se encontró columna de predicción (smiles) en {sub_path.name}. Cabecera: {header}",
                hook_id="H24"
            )

        seen_mols = set()
        for line_no, row in enumerate(reader, start=2):
            if not row or not any(row):
                continue
            mol_id = row[0].strip()
            if not mol_id:
                common.block(f"molecule_id vacío en línea {line_no} de {sub_path.name}", hook_id="H24")
            if mol_id in seen_mols:
                common.block(f"molecule_id duplicado '{mol_id}' en línea {line_no} de {sub_path.name}", hook_id="H24")
            seen_mols.add(mol_id)

            if len(row) != len(header):
                common.block(
                    f"Fila {line_no} tiene {len(row)} columnas (esperadas {len(header)}). Posible uso de coma ',' en lugar de punto y coma ';'.",
                    hook_id="H24",
                    reason="La fila no respeta la estructura de 2 columnas requerida por Kaggle.",
                    solution="Separa los candidatos usando ';' y asegúrate de no generar columnas adicionales."
                )

            cand_str = row[smiles_idx].strip() if len(row) > smiles_idx else ""
            if not cand_str:
                common.block(f"Predicción vacía para molecule_id '{mol_id}' en línea {line_no}", hook_id="H24")

            if sep == ";" and "," in cand_str:
                common.block(
                    f"Fila {line_no} contiene comas ',' en el campo de candidatos. El separador obligatorio es ';'.",
                    hook_id="H24",
                    reason="Kaggle espera una única columna de candidatos delimitada por ';'.",
                    solution="Usa ';' como separador entre SMILES."
                )

            candidates = [c.strip() for c in cand_str.split(sep) if c.strip()]
            if len(candidates) > max_candidates:
                common.block(
                    f"Fila {line_no} ('{mol_id}') contiene {len(candidates)} candidatos (> {max_candidates} permitidos)",
                    hook_id="H24",
                    reason="Kaggle descarta submissions con más de 25 candidatos por molécula.",
                    solution=f"Trunca la lista a un máximo de {max_candidates} candidatos."
                )

            # Comprobar duplicados textuales en la fila
            if len(candidates) != len(set(candidates)):
                common.block(
                    f"Fila {line_no} ('{mol_id}') contiene candidatos SMILES duplicados dentro del top-25.",
                    hook_id="H24",
                    reason="Los duplicados desperdician slots del top-25 y degradan el MRR@25.",
                    solution="Deduplica los candidatos preservando el orden de mejor probabilidad."
                )


def main():
    payload = common.read_stdin_payload()
    config = common.load_project_config()
    max_cands = config.get("max_candidates", 25)
    sep = config.get("candidate_separator", ";")

    root = common.find_project_root() or Path.cwd()

    # Buscar submission.csv en paths pasados o en la raíz/reports
    sub_candidates = [
        root / "submission.csv",
        root / "reports" / "submission.csv",
    ]
    for p in payload.get("paths", []):
        sub_candidates.append(Path(p))

    for sc in sub_candidates:
        if sc.is_file() and sc.name.endswith(".csv") and "submission" in sc.name.lower():
            validate_file(sc, max_cands, sep)

    sys.exit(0)


if __name__ == "__main__":
    main()
