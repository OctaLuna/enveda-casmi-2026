"""Adduct normalization and exact neutral mass calculation for CASMI 2026.

Uses high-resolution monoisotopic ion masses (accounting for electron mass)
for Bruker timsTOF positive and negative ion modes.
"""

from __future__ import annotations

import logging

logger = logging.getLogger(__name__)

# Fundamental constants (IUPAC / NIST)
ELECTRON_MASS = 0.00054857990946
PROTON_MASS = 1.00727646688

MONOISOTOPIC_MASSES = {
    "H": 1.00782503223,
    "C": 12.0,
    "N": 14.00307400443,
    "O": 15.99491461957,
    "Na": 22.9897692820,
    "K": 38.9637064864,
    "Cl": 34.968852682,
}

H2O_MASS = 2 * MONOISOTOPIC_MASSES["H"] + MONOISOTOPIC_MASSES["O"]
NA_ION = MONOISOTOPIC_MASSES["Na"] - ELECTRON_MASS
K_ION = MONOISOTOPIC_MASSES["K"] - ELECTRON_MASS
NH4_ION = MONOISOTOPIC_MASSES["N"] + 4 * MONOISOTOPIC_MASSES["H"] - ELECTRON_MASS
CL_ION = MONOISOTOPIC_MASSES["Cl"] + ELECTRON_MASS
# Formate anion [HCOO]- = HCOOH - H+
FORMATE_ION = (
    2 * MONOISOTOPIC_MASSES["H"]
    + MONOISOTOPIC_MASSES["C"]
    + 2 * MONOISOTOPIC_MASSES["O"]
    - PROTON_MASS
)

# Mapping of adduct -> (n_molecules, charge_magnitude, net_mass_delta)
# Formula: mz = (n * M + delta) / |z| => M = (mz * |z| - delta) / n
ADDUCT_MAP: dict[str, tuple[int, int, float]] = {
    # Positive ion mode
    "[M+H]+": (1, 1, PROTON_MASS),
    "[M+Na]+": (1, 1, NA_ION),
    "[M+K]+": (1, 1, K_ION),
    "[M+NH4]+": (1, 1, NH4_ION),
    "[M+H-H2O]+": (1, 1, PROTON_MASS - H2O_MASS),
    "[M+2H]2+": (1, 2, 2 * PROTON_MASS),
    "[2M+H]+": (2, 1, PROTON_MASS),
    # Negative ion mode
    "[M-H]-": (1, 1, -PROTON_MASS),
    "[M-H-H2O]-": (1, 1, -PROTON_MASS - H2O_MASS),
    "[M+Cl]-": (1, 1, CL_ION),
    "[M+FA-H]-": (1, 1, FORMATE_ION),
}


def normalize_adduct_string(adduct: str) -> str:
    """Normalize adduct representation by stripping whitespace.

    Args:
        adduct: Raw adduct string (e.g. "[M + H]+").

    Returns:
        Normalized string (e.g. "[M+H]+").
    """
    if not adduct:
        return ""
    return adduct.replace(" ", "").strip()


def calculate_neutral_mass(precursor_mz: float, adduct: str) -> float | None:
    """Calculate exact neutral monoisotopic mass M from precursor m/z and adduct.

    Args:
        precursor_mz: Precursor ion mass-to-charge ratio.
        adduct: Adduct annotation (e.g., '[M+H]+', '[M-H]-').

    Returns:
        Exact neutral mass M in Daltons, or None if adduct is unrecognized or invalid.
    """
    key = normalize_adduct_string(adduct)
    if key not in ADDUCT_MAP:
        logger.debug("Unknown or unsupported adduct: '%s'", adduct)
        return None

    n, z, delta = ADDUCT_MAP[key]
    if n <= 0 or z <= 0:
        return None

    return (precursor_mz * z - delta) / n

