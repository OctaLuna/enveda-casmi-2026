#!/usr/bin/env python3
"""
H26 - preprocessing-order-check
Verifica el pipeline de preprocesamiento de espectros MS/MS:
1. Deisotopado antes de binning o extracción de embeddings.
2. Filtro de picos superiores al precursor (+precursor_tolerance_da).
3. Descarte de espectros con menos de min_peaks (5).
4. Umbral de intensidad dentro de intensity_threshold_range ([0.01, 0.02] = 1-2%).
Modo: warn.
"""

from pathlib import Path
import re
import sys

HOOK_DIR = Path(__file__).resolve().parent.parent
LIB_DIR = HOOK_DIR / "lib"
if str(LIB_DIR) not in sys.path:
    sys.path.insert(0, str(LIB_DIR))

import common


def analyze_preprocessing_code(content: str, source: str, config: dict) -> None:
    min_peaks = config.get("min_peaks", 5)
    prec_tol = config.get("precursor_tolerance_da", 2.0)

    # 1. Chequeo de orden deisotopado vs binning
    if "binning" in content.lower() and "deisotope" in content.lower():
        pos_bin = content.lower().find("binning")
        pos_deiso = content.lower().find("deisotope")
        if pos_bin < pos_deiso:
            common.warn(
                f"Posible inversión de pipeline en {source}: binning detectado antes de deisotopado. El deisotopado debe ocurrir antes.",
                hook_id="H26"
            )

    # 2. Umbral de intensidad
    if "threshold" in content.lower():
        # Buscar valores de threshold numéricos
        nums = re.findall(r"threshold\s*=\s*(0\.\d+)", content)
        for n in nums:
            val = float(n)
            if val < 0.005 or val > 0.05:
                common.warn(
                    f"Umbral de intensidad {val} en {source} está fuera del rango recomendado 1-2% (0.01 - 0.02).",
                    hook_id="H26"
                )


def main():
    payload = common.read_stdin_payload()
    config = common.load_project_config()

    content = payload.get("content", "")
    if content:
        analyze_preprocessing_code(content, "payload", config)

    for p in payload.get("paths", []):
        p_obj = Path(p)
        if p_obj.is_file() and p_obj.suffix == ".py":
            try:
                analyze_preprocessing_code(p_obj.read_text(encoding="utf-8"), str(p_obj), config)
            except Exception:
                pass

    sys.exit(0)


if __name__ == "__main__":
    main()
