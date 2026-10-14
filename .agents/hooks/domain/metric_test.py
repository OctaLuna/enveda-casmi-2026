#!/usr/bin/env python3
"""
H23 - metric-test
Ejecuta casos de prueba fijos sobre la métrica oficial MRR@25:
- Rank 1 -> 1.0
- Rank 2 -> 0.5
- Rank 25 -> 0.04 (1/25)
- Fuera de top 25 (ej. rank 26) -> 0.0
- Solo cuenta la primera coincidencia
- Candidatos duplicados no inflan el ranking
"""

from pathlib import Path
import sys

HOOK_DIR = Path(__file__).resolve().parent.parent
LIB_DIR = HOOK_DIR / "lib"
if str(LIB_DIR) not in sys.path:
    sys.path.insert(0, str(LIB_DIR))

import common


def test_metric_implementation(root: Path) -> None:
    src_dir = root / "src"
    if str(src_dir) not in sys.path:
        sys.path.insert(0, str(src_dir))

    try:
        from utils.metrics import calculate_mrr_at_25
    except ImportError:
        # Si aún no existe el módulo, omitir sin bloquear
        return

    # Caso 1: Rank 1 perfecto
    gt1 = ["MOL_A"]
    preds1 = [["MOL_A", "MOL_B", "MOL_C"]]
    score1 = calculate_mrr_at_25(gt1, preds1)
    if abs(score1 - 1.0) > 1e-5:
        common.block(f"Rank 1 esperado 1.0, obtenido {score1}", hook_id="H23")

    # Caso 2: Rank 2
    gt2 = ["MOL_B"]
    preds2 = [["MOL_A", "MOL_B", "MOL_C"]]
    score2 = calculate_mrr_at_25(gt2, preds2)
    if abs(score2 - 0.5) > 1e-5:
        common.block(f"Rank 2 esperado 0.5, obtenido {score2}", hook_id="H23")

    # Caso 3: Rank 25
    preds_25 = [f"DUMMY_{i}" for i in range(24)] + ["TARGET_MOL"]
    score25 = calculate_mrr_at_25(["TARGET_MOL"], [preds_25])
    if abs(score25 - 0.04) > 1e-5:
        common.block(f"Rank 25 esperado 0.04, obtenido {score25}", hook_id="H23")

    # Caso 4: Fuera de top 25 (Rank 26)
    preds_26 = [f"DUMMY_{i}" for i in range(25)] + ["TARGET_MOL"]
    score26 = calculate_mrr_at_25(["TARGET_MOL"], [preds_26])
    if abs(score26 - 0.0) > 1e-5:
        common.block(f"Rank 26 fuera de top 25 esperado 0.0, obtenido {score26}", hook_id="H23")

    # Caso 5: Solo primera coincidencia (duplicados no suman)
    preds_dup = [["MOL_X", "TARGET", "TARGET", "MOL_Y"]]
    score_dup = calculate_mrr_at_25(["TARGET"], preds_dup)
    if abs(score_dup - 0.5) > 1e-5:
        common.block(f"Primera coincidencia duplicada esperada 0.5, obtenido {score_dup}", hook_id="H23")


def main():
    payload = common.read_stdin_payload()
    config = common.load_project_config()
    root = common.find_project_root() or Path.cwd()

    test_metric_implementation(root)
    sys.exit(0)


if __name__ == "__main__":
    main()
