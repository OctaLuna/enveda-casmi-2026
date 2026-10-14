#!/usr/bin/env python3
"""
H30 - seed-determinism
Inspecciona código de entrenamiento, muestreo y generación de splits para verificar
que todas las operaciones estocásticas estén controladas por una semilla determinista
(src.utils.reproducibility.set_seed, random_state=, seed=).
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

STOCHASTIC_PATTERNS = [
    r"\btrain_test_split\s*\(",
    r"\bGroupKFold\s*\(",
    r"\bKFold\s*\(",
    r"\bnp\.random\.",
    r"\brandom\.(shuffle|sample|choice)",
    r"\btorch\.(randn|rand|randint)",
]

SEED_PATTERNS = [
    r"\bset_seed\s*\(",
    r"\brandom_state\s*=\s*\d+",
    r"\bseed\s*=\s*\d+",
    r"\btorch\.manual_seed\s*\(",
]


def check_code(content: str, source: str) -> None:
    has_stochastic = any(re.search(pat, content) for pat in STOCHASTIC_PATTERNS)
    if has_stochastic:
        has_seed = any(re.search(pat, content) for pat in SEED_PATTERNS)
        if not has_seed:
            common.warn(
                f"Operaciones aleatorias detectadas en {source} sin una semilla fija explícita (set_seed, random_state, seed).",
                hook_id="H30"
            )


def main():
    payload = common.read_stdin_payload()
    config = common.load_project_config()

    content = payload.get("content", "")
    if content:
        check_code(content, "payload")

    for p in payload.get("paths", []):
        p_obj = Path(p)
        if p_obj.is_file() and p_obj.suffix == ".py":
            try:
                check_code(p_obj.read_text(encoding="utf-8"), str(p_obj))
            except Exception:
                pass

    sys.exit(0)


if __name__ == "__main__":
    main()

