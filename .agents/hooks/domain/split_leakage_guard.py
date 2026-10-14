#!/usr/bin/env python3
"""
H22 - split-leakage-guard
Verifica que las particiones de validación eviten fugas de datos (data leakage):
1. Partición estricta por molecule_id, nunca por spectrum_id.
2. Intersección nula de molecule_id entre train y validación.
3. Existencia de los 3 subsets: Val-Clase1, Val-Clase2 y Val-Clase3.
4. Registro de al menos 3 semillas para validación robusta (min_seeds).
"""

import json
from pathlib import Path
import re
import sys

HOOK_DIR = Path(__file__).resolve().parent.parent
LIB_DIR = HOOK_DIR / "lib"
if str(LIB_DIR) not in sys.path:
    sys.path.insert(0, str(LIB_DIR))

import common


def check_code_for_spectrum_split(content: str, source: str) -> None:
    if re.search(r"split.*?\(\s*.*?(spectrum_id|spectrum_idx)", content, re.IGNORECASE):
        common.block(
            f"Fuga potencial detectada: partición por spectrum_id en {source}",
            hook_id="H22",
            reason="Múltiples espectros de la misma molécula distribuidos entre train y val causan data leakage masivo.",
            solution="Agrupa siempre las particiones por molecule_id utilizando GroupKFold o partición estructural."
        )


def check_splits_directory(splits_dir: Path, min_seeds: int) -> None:
    if not splits_dir.is_dir():
        return

    metadata_files = list(splits_dir.glob("*.json"))
    if not metadata_files:
        return

    for meta_file in metadata_files:
        try:
            with open(meta_file, "r", encoding="utf-8") as f:
                data = json.load(f)

            # Verificar semillas
            seeds = data.get("seeds", [])
            if isinstance(seeds, list) and len(seeds) < min_seeds:
                common.warn(
                    f"{meta_file.name} contiene {len(seeds)} semillas registradas (< {min_seeds}). Se exigen al menos {min_seeds}.",
                    hook_id="H22"
                )

            # Verificar clases
            subsets = data.get("subsets", {}) or data.get("classes", {})
            if isinstance(subsets, dict):
                required_subsets = {"val_clase1", "val_clase2", "val_clase3"}
                found = {k.lower().replace("-", "_") for k in subsets.keys()}
                if not required_subsets.issubset(found):
                    common.warn(
                        f"{meta_file.name} no define explícitamente los 3 subsets requeridos: {required_subsets}",
                        hook_id="H22"
                    )

            # Verificar disyunción de conjuntos si se incluyen listas de molecule_id
            train_mols = set(data.get("train_molecule_ids", []))
            val_mols = set(data.get("val_molecule_ids", []))
            if train_mols and val_mols:
                overlap = train_mols.intersection(val_mols)
                if overlap:
                    common.block(
                        f"¡Fuga crítica de datos! {len(overlap)} molecule_id compartidos entre train y val en {meta_file.name}.",
                        hook_id="H22",
                        reason="Intersección no vacía entre conjunto de entrenamiento y conjunto de validación.",
                        solution="Aísla estrictamente los identificadores de moléculas en particiones disjuntas."
                    )
        except Exception as e:
            common.log_error("H22.check_splits", f"Error leyendo {meta_file}: {e}")


def main():
    payload = common.read_stdin_payload()
    config = common.load_project_config()
    min_seeds = config.get("min_seeds", 3)

    # 1. Comprobar archivos o contenido pasados
    content = payload.get("content", "")
    if content:
        check_code_for_spectrum_split(content, "payload")

    for p in payload.get("paths", []):
        p_obj = Path(p)
        if p_obj.is_file() and p_obj.suffix == ".py":
            try:
                check_code_for_spectrum_split(p_obj.read_text(encoding="utf-8"), str(p_obj))
            except Exception:
                pass
        elif p_obj.is_file() and p_obj.suffix == ".json":
            try:
                with open(p_obj, "r", encoding="utf-8") as f:
                    data = json.load(f)
                train_mols = set(data.get("train_molecule_ids", []))
                val_mols = set(data.get("val_molecule_ids", []))
                if train_mols and val_mols:
                    overlap = train_mols.intersection(val_mols)
                    if overlap:
                        common.block(
                            f"¡Fuga crítica de datos! {len(overlap)} molecule_id compartidos entre train y val en {p_obj.name}.",
                            hook_id="H22",
                            reason="Intersección no vacía entre conjunto de entrenamiento y conjunto de validación.",
                            solution="Aísla estrictamente los identificadores de moléculas en particiones disjuntas."
                        )
            except Exception as e:
                common.log_error("H22.check_splits", f"Error leyendo {p_obj}: {e}")

    # 2. Comprobar directorio data/splits
    root = common.find_project_root() or Path.cwd()
    check_splits_directory(root / "data" / "splits", min_seeds)
    check_splits_directory(root / "splits", min_seeds)

    sys.exit(0)


if __name__ == "__main__":
    main()
