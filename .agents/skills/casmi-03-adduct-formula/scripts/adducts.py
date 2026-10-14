"""Aductos -> masa neutra y descomposición de fórmula (CHNOPS + halógenos opcionales).

Masas monoisotópicas. Las masas de iones restan la masa del electrón.
Verifica la tabla contra los aductos reales presentes en train/test antes de usarla.
"""
from __future__ import annotations

from typing import Dict, List, Optional, Sequence, Tuple

import numpy as np

ELECTRON = 0.00054857990946
PROTON = 1.00727646688
MONO = {
    "C": 12.0, "H": 1.00782503223, "N": 14.00307400443, "O": 15.99491461957,
    "P": 30.97376199842, "S": 31.9720711744, "F": 18.99840316273,
    "Cl": 34.968852682, "Br": 78.9183376, "I": 126.9044719,
    "Na": 22.9897692820, "K": 38.9637064864,
}
H2O = 2 * MONO["H"] + MONO["O"]
NA_ION = MONO["Na"] - ELECTRON
K_ION = MONO["K"] - ELECTRON
NH4_ION = MONO["N"] + 4 * MONO["H"] - ELECTRON
CL_ION = MONO["Cl"] + ELECTRON

# adducto -> (n_M, |carga|, masa neta añadida). mz = (n*M + delta) / |z|
ADDUCTS: Dict[str, Tuple[int, int, float]] = {
    "[M+H]+": (1, 1, PROTON),
    "[M+Na]+": (1, 1, NA_ION),
    "[M+K]+": (1, 1, K_ION),
    "[M+NH4]+": (1, 1, NH4_ION),
    "[M+H-H2O]+": (1, 1, PROTON - H2O),
    "[M+2H]2+": (1, 2, 2 * PROTON),
    "[2M+H]+": (2, 1, PROTON),
    "[M-H]-": (1, 1, -PROTON),
    "[M-H-H2O]-": (1, 1, -PROTON - H2O),
    "[M+Cl]-": (1, 1, CL_ION),
    # [M+FA-H]- = M + HCOOH - H+  (HCOOH = 2H + C + 2O)
    "[M+FA-H]-": (1, 1, (2 * MONO["H"] + MONO["C"] + 2 * MONO["O"]) - PROTON),
}


def normalize_adduct(adduct: str) -> str:
    return adduct.replace(" ", "").strip()


def neutral_mass(mz: float, adduct: str) -> Optional[float]:
    """Masa neutra M desde m/z y aducto. None si el aducto es desconocido."""
    key = normalize_adduct(adduct)
    if key not in ADDUCTS:
        return None
    n, z, delta = ADDUCTS[key]
    return (mz * z - delta) / n


def hill_formula(counts: Dict[str, int]) -> str:
    order = ["C", "H"] + sorted(e for e in counts if e not in ("C", "H"))
    return "".join(f"{e}{counts[e] if counts[e] > 1 else ''}" for e in order if counts.get(e, 0) > 0)


def decompose(
    M: float,
    ppm: float = 5.0,
    bounds: Optional[Dict[str, Tuple[int, int]]] = None,
    halogens: Sequence[Tuple[int, int, int, int]] = ((0, 0, 0, 0),),
) -> List[dict]:
    """Fórmulas candidatas para la masa neutra M.

    halogens: combinaciones (F, Cl, Br, I) a probar; por defecto solo CHNOPS.
    Filtros: error en ppm, H >= 0, DBE >= 0 y entero (regla del nitrógeno incluida).
    """
    b = {"C": (1, 80), "N": (0, 15), "O": (0, 25), "P": (0, 3), "S": (0, 4)}
    b.update(bounds or {})
    axes = [np.arange(b[e][0], b[e][1] + 1) for e in "CNOPS"]
    C, N, O, P, S = np.meshgrid(*axes, indexing="ij")
    heavy_base = (C * MONO["C"] + N * MONO["N"] + O * MONO["O"]
                  + P * MONO["P"] + S * MONO["S"])
    results: List[dict] = []
    for f, cl, br, i in halogens:
        X = f + cl + br + i
        hv = heavy_base + f * MONO["F"] + cl * MONO["Cl"] + br * MONO["Br"] + i * MONO["I"]
        H = np.rint((M - hv) / MONO["H"]).astype(int)
        mass = hv + H * MONO["H"]
        err = (mass - M) / M * 1e6
        dbe2 = 2 * C + 2 + N + P - H - X  # 2 * DBE
        ok = (H >= 0) & (np.abs(err) <= ppm) & (dbe2 >= 0) & (dbe2 % 2 == 0)
        for idx in zip(*np.nonzero(ok)):
            counts = {"C": int(C[idx]), "H": int(H[idx]), "N": int(N[idx]),
                      "O": int(O[idx]), "P": int(P[idx]), "S": int(S[idx]),
                      "F": f, "Cl": cl, "Br": br, "I": i}
            results.append({
                "formula": hill_formula(counts),
                "counts": counts,
                "ppm_error": float(err[idx]),
                "dbe": float(dbe2[idx] / 2),
            })
    results.sort(key=lambda r: abs(r["ppm_error"]))
    return results


if __name__ == "__main__":
    # Prueba: cafeína C8H10N4O2, M = 194.080376; [M+H]+ = 195.087652
    mz = 195.087652
    M = neutral_mass(mz, "[M+H]+")
    assert abs(M - 194.080376) < 1e-4, M
    hits = decompose(M, ppm=3)
    assert any(h["formula"] == "C8H10N4O2" for h in hits)
    print("adducts selftest OK; candidatos:", [h["formula"] for h in hits[:5]])

