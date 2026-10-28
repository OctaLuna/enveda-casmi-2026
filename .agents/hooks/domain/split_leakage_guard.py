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


def _validate_manifest(manifest_path: Path, max_bytes: int) -> int:
    if manifest_path.stat().st_size > max_bytes:
        common.block(
            f"{manifest_path.name} exceeds {max_bytes} bytes.",
            hook_id="H22",
            reason="Split manifests must respect the project file-size limit.",
        )
    try:
        data = json.loads(manifest_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        common.block(f"Invalid JSON in {manifest_path.name}: {exc}", hook_id="H22")

    if not isinstance(data, dict):
        common.block(
            f"Manifest root must be an object in {manifest_path.name}.",
            hook_id="H22",
        )
    if data.get("schema_version") != 1:
        common.block(f"Unsupported schema in {manifest_path.name}.", hook_id="H22")
    metadata = data.get("metadata")
    if not isinstance(metadata, dict):
        common.block(f"Missing metadata in {manifest_path.name}.", hook_id="H22")
    seed = metadata.get("seed")
    if seed not in (42, 1337, 2026):
        common.block(f"Unexpected seed in {manifest_path.name}.", hook_id="H22")
    if manifest_path.name.startswith("split_seed_") and manifest_path.name != f"split_seed_{seed}.json":
        common.block(f"Filename and seed differ in {manifest_path.name}.", hook_id="H22")

    keys = (
        "train_molecule_ids",
        "val_clase1_molecule_ids",
        "val_clase1_query_spectrum_ids",
        "val_clase2_molecule_ids",
        "val_clase3_molecule_ids",
        "val_clase3_excluded_neighbor_molecule_ids",
    )
    sets = {}
    for key in keys:
        value = data.get(key)
        if not isinstance(value, list) or any(not isinstance(item, str) for item in value):
            common.block(f"Invalid list {key} in {manifest_path.name}.", hook_id="H22")
        if len(value) != len(set(value)):
            common.block(f"Duplicate IDs in {key} of {manifest_path.name}.", hook_id="H22")
        sets[key] = set(value)

    train = sets["train_molecule_ids"]
    val1 = sets["val_clase1_molecule_ids"]
    val2 = sets["val_clase2_molecule_ids"]
    val3 = sets["val_clase3_molecule_ids"]
    excluded = sets["val_clase3_excluded_neighbor_molecule_ids"]
    if not train or not val1 or not val2 or not val3:
        common.block(f"Missing a required partition in {manifest_path.name}.", hook_id="H22")
    if not val1 <= train or train & val2 or train & val3 or val2 & val3:
        common.block(f"Partition leakage in {manifest_path.name}.", hook_id="H22")
    if excluded & (train | val1 | val2 | val3):
        common.block(f"Excluded-neighbor overlap in {manifest_path.name}.", hook_id="H22")

    queries = data["val_clase1_query_spectrum_ids"]
    if not queries or len(queries) != len(val1):
        common.block(f"Expected one Class 1 query per molecule in {manifest_path.name}.", hook_id="H22")
    if any(key.endswith("spectrum_ids") and key != "val_clase1_query_spectrum_ids" for key in data):
        common.block(f"Full spectrum ID arrays are not allowed in {manifest_path.name}.", hook_id="H22")

    expected_counts = {
        "n_train_molecules": len(train),
        "n_val_clase1_molecules": len(val1),
        "n_val_clase2_molecules": len(val2),
        "n_val_clase3_molecules": len(val3),
    }
    if any(metadata.get(key) != count for key, count in expected_counts.items()):
        common.block(f"Inconsistent counts in {manifest_path.name}.", hook_id="H22")
    distance = metadata.get("mean_val_clase3_nearest_train_tanimoto_distance")
    if not isinstance(distance, (int, float)) or distance <= 0.60:
        common.block(f"Tanimoto distance criterion failed in {manifest_path.name}.", hook_id="H22")
    if not re.fullmatch(r"[0-9a-fA-F]{64}", str(metadata.get("train_sha256", ""))):
        common.block(f"Missing train SHA-256 in {manifest_path.name}.", hook_id="H22")
    return seed


def check_splits_directory(
    splits_dir: Path, min_seeds: int, require_manifests: bool = False
) -> None:
    expected = {f"split_seed_{seed}.json" for seed in (42, 1337, 2026)}
    if not splits_dir.is_dir():
        if require_manifests:
            common.block(f"Missing split directory: {splits_dir}.", hook_id="H22")
        return
    files = sorted(splits_dir.glob("split_seed_*.json"))
    names = {item.name for item in files}
    if require_manifests and names != expected:
        common.block(
            f"Expected exactly three split manifests; found {sorted(names)}.",
            hook_id="H22",
        )
    if not files:
        if require_manifests:
            common.block("No split manifests were generated.", hook_id="H22")
        return
    if len(files) < min_seeds:
        common.warn(f"Only {len(files)} split manifests found.", hook_id="H22")
    config = common.load_project_config()
    max_bytes = int(config.get("large_file_mb", 25)) * 1024 * 1024
    seeds = {_validate_manifest(item, max_bytes) for item in files}
    if require_manifests and seeds != {42, 1337, 2026}:
        common.block("Split manifests do not contain all required seeds.", hook_id="H22")


def _split_task_is_complete(root: Path) -> bool:
    task_file = root / "specs" / "001_model_baseline" / "tasks.md"
    if not task_file.is_file():
        return False
    return bool(re.search(
        r"^\s*-\s*\[x\].*\[DEV1-T3\.3\]",
        task_file.read_text(encoding="utf-8"),
        flags=re.IGNORECASE | re.MULTILINE,
    ))


def main():
    payload = common.read_stdin_payload()
    config = common.load_project_config()
    min_seeds = config.get("min_seeds", 3)
    root = common.find_project_root() or Path.cwd()
    content = payload.get("content", "")
    if content:
        check_code_for_spectrum_split(content, "payload")

    paths = payload.get("paths", [])
    for path_value in paths:
        path_obj = Path(path_value)
        if path_obj.is_file() and path_obj.suffix == ".py":
            try:
                check_code_for_spectrum_split(path_obj.read_text(encoding="utf-8"), str(path_obj))
            except OSError:
                pass
        elif path_obj.is_file() and path_obj.suffix == ".json":
            _validate_manifest(
                path_obj, int(config.get("large_file_mb", 25)) * 1024 * 1024
            )
        elif path_obj.is_dir():
            check_splits_directory(path_obj, min_seeds, require_manifests=True)

    touched = any(
        "data/splits" in item.replace("\\", "/")
        or Path(item).name.startswith("split_seed_")
        for item in paths
    )
    check_splits_directory(
        root / "data" / "splits",
        min_seeds,
        require_manifests=touched or _split_task_is_complete(root),
    )
    check_splits_directory(root / "splits", min_seeds)
    sys.exit(0)


if __name__ == "__main__":
    main()
