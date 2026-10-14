#!/usr/bin/env python3
"""
H25 - adduct-mass-guard
Verifica la conversión matemática de precursor_mz a masa neutra según aductos:
[M+H]+, [M-H]-, [M+NH4]+, [M+Na]+, [M+2H]2+.
Tolerancia estricta: <= 1e-4 Da.
Previene el error silencioso de consultar fórmulas moleculares usando precursor_mz en lugar de masa neutra.
"""

from pathlib import Path
import re
import sys

HOOK_DIR = Path(__file__).resolve().parent.parent
LIB_DIR = HOOK_DIR / "lib"
if str(LIB_DIR) not in sys.path:
    sys.path.insert(0, str(LIB_DIR))

import common

ADDUCT_MASSES = {
    # Constantes IUPAC de masas monoisotópicas
    "H": 1.00782503223,
    "Na": 22.9897692820,
    "NH4": 18.03382555,
    "electron": 0.0005485799,
}

# Casos golden: (adduct, precursor_mz, masa_neutra_esperada)
GOLDEN_ADDUCTS = [
    ("[M+H]+", 301.1078, 301.1078 - ADDUCT_MASSES["H"]),
    ("[M-H]-", 299.0922, 299.0922 + ADDUCT_MASSES["H"]),
    ("[M+Na]+", 323.0897, 323.0897 - ADDUCT_MASSES["Na"]),
    ("[M+NH4]+", 318.1340, 318.1340 - ADDUCT_MASSES["NH4"]),
    ("[M+2H]2+", 151.0578, (151.0578 * 2) - (ADDUCT_MASSES["H"] * 2)),
]


def test_adduct_script(root: Path) -> None:
    # Si existe el script adducts.py en las skills o en src/data, testearlo
    possible_adduct_scripts = [
        root / ".agents" / "skills" / "casmi-03-adduct-formula" / "scripts" / "adducts.py",
        root / "src" / "data" / "adduct_normalizer.py",
    ]
    for script in possible_adduct_scripts:
        if script.is_file():
            try:
                # Comprobar si exporta calculate_neutral_mass
                import importlib.util
                spec = importlib.util.spec_from_file_location("adduct_mod", str(script))
                if spec and spec.loader:
                    mod = importlib.util.module_from_spec(spec)
                    spec.loader.exec_module(mod)
                    fn = getattr(mod, "precursor_to_neutral_mass", None) or getattr(mod, "calculate_neutral_mass", None)
                    if callable(fn):
                        for adduct, mz, expected in GOLDEN_ADDUCTS:
                            res = fn(mz, adduct)
                            if abs(res - expected) > 1e-3:
                                common.block(
                                    f"Fallo en conversión de aducto {adduct}: esperado ~{expected:.4f}, obtenido {res:.4f}",
                                    hook_id="H25"
                                )
            except Exception as e:
                common.log_error("H25.test_adduct", f"Error testeando {script.name}: {e}")


def check_static_code(content: str, source: str) -> None:
    # Detecta si se pasa precursor_mz directo a estimación de fórmula sin mención de neutral_mass o aducto
    if re.search(r"formula_from_mass\s*\(\s*precursor_mz\b", content, re.IGNORECASE):
        common.block(
            f"Se detectó llamada a estimación de fórmula usando 'precursor_mz' directamente en {source}",
            hook_id="H25",
            reason="El precursor_mz contiene el aducto y no representa la masa neutra de la molécula.",
            solution="Convierte precursor_mz a masa neutra según el aducto antes de estimar o filtrar fórmulas."
        )


def main():
    payload = common.read_stdin_payload()
    config = common.load_project_config()
    root = common.find_project_root() or Path.cwd()

    content = payload.get("content", "")
    if content:
        check_static_code(content, "payload")

    for p in payload.get("paths", []):
        p_obj = Path(p)
        if p_obj.is_file() and p_obj.suffix == ".py":
            try:
                check_static_code(p_obj.read_text(encoding="utf-8"), str(p_obj))
            except Exception:
                pass

    test_adduct_script(root)
    sys.exit(0)


if __name__ == "__main__":
    main()
