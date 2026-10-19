"""Exact molecular formula estimator for high-resolution MS/MS in CASMI 2026.

Decomposes exact neutral mass M into candidate elemental formulas (CHNOPS + halogens)
within high-precision ppm tolerance, applying Senior's chemical rules and DBE validation.
"""

from __future__ import annotations

import logging
import math
from collections.abc import Sequence
from dataclasses import dataclass

import numpy as np

from src.data.chemical_filters import calculate_dbe, is_chemically_valid_formula

logger = logging.getLogger(__name__)

# IUPAC high-precision monoisotopic atomic masses in Daltons
MONO_MASSES: dict[str, float] = {
    "C": 12.0,
    "H": 1.00782503223,
    "N": 14.00307400443,
    "O": 15.99491461957,
    "P": 30.97376199842,
    "S": 31.9720711744,
    "F": 18.99840316273,
    "Cl": 34.968852682,
    "Br": 78.9183376,
    "I": 126.9044719,
}


def hill_formula(counts: dict[str, int]) -> str:
    """Format an element count mapping into standard Hill system notation.

    Carbon first, Hydrogen second, then remaining elements in alphabetical order.

    Args:
        counts: Mapping from element symbol to integer count.

    Returns:
        Formatted formula string (e.g. "C8H10N4O2").
    """
    elements = []
    # Carbon first
    if counts.get("C", 0) > 0:
        c = counts["C"]
        elements.append(f"C{c if c > 1 else ''}")

    # Hydrogen second
    if counts.get("H", 0) > 0:
        h = counts["H"]
        elements.append(f"H{h if h > 1 else ''}")

    # Other elements in alphabetical order
    other_elements = sorted(
        [e for e in counts if e not in ("C", "H") and counts[e] > 0]
    )
    for el in other_elements:
        cnt = counts[el]
        elements.append(f"{el}{cnt if cnt > 1 else ''}")

    return "".join(elements)


@dataclass
class CandidateFormula:
    """Represents a predicted elemental molecular formula candidate."""

    formula: str
    counts: dict[str, int]
    exact_mass: float
    ppm_error: float
    dbe: float
    confidence_score: float


class FormulaEstimator:
    """Generates and ranks candidate molecular formulas for exact neutral mass M."""

    def __init__(
        self,
        ppm_tolerance: float = 7.0,
        allow_halogens: bool = False,
    ):
        self.ppm_tolerance = ppm_tolerance
        self.allow_halogens = allow_halogens

    def estimate_formulas(
        self,
        neutral_mass: float,
        ppm_tolerance: float | None = None,
        max_candidates: int = 50,
    ) -> list[CandidateFormula]:
        """Estimate candidate formulas for a given neutral analyte mass M.

        Args:
            neutral_mass: Exact neutral monoisotopic mass in Daltons.
            ppm_tolerance: Mass tolerance in ppm (defaults to class setting).
            max_candidates: Maximum number of candidate formulas to return.

        Returns:
            List of CandidateFormula objects ordered by descending confidence score.
        """
        tol_ppm = self.ppm_tolerance if ppm_tolerance is None else ppm_tolerance
        if neutral_mass <= 0.0 or tol_ppm <= 0.0:
            logger.warning(
                "Invalid neutral_mass (%.4f) or ppm_tolerance (%.2f)",
                neutral_mass,
                tol_ppm,
            )
            return []

        # Determine search bounds
        max_c = min(80, int(neutral_mass // MONO_MASSES["C"]))
        max_n = min(15, int(neutral_mass // MONO_MASSES["N"]))
        max_o = min(25, int(neutral_mass // MONO_MASSES["O"]))
        max_p = min(3, int(neutral_mass // MONO_MASSES["P"]))
        max_s = min(4, int(neutral_mass // MONO_MASSES["S"]))

        halogen_combinations: Sequence[tuple[int, int, int, int]] = (
            ((0, 0, 0, 0),)
            if not self.allow_halogens
            else (
                (0, 0, 0, 0),
                (1, 0, 0, 0),  # 1 F
                (0, 1, 0, 0),  # 1 Cl
                (0, 2, 0, 0),  # 2 Cl
                (0, 0, 1, 0),  # 1 Br
                (0, 0, 0, 1),  # 1 I
            )
        )

        candidates: list[CandidateFormula] = []

        # Meshgrid / nested loop over heavy atoms
        for f, cl, br, i_hal in halogen_combinations:
            hal_mass = (
                f * MONO_MASSES["F"]
                + cl * MONO_MASSES["Cl"]
                + br * MONO_MASSES["Br"]
                + i_hal * MONO_MASSES["I"]
            )
            if hal_mass >= neutral_mass:
                continue

            for c in range(1, max_c + 1):
                mass_c = c * MONO_MASSES["C"] + hal_mass
                if mass_c >= neutral_mass:
                    break

                for n in range(max_n + 1):
                    mass_cn = mass_c + n * MONO_MASSES["N"]
                    if mass_cn >= neutral_mass:
                        break

                    for o in range(max_o + 1):
                        mass_cno = mass_cn + o * MONO_MASSES["O"]
                        if mass_cno >= neutral_mass:
                            break

                        for p in range(max_p + 1):
                            mass_cnop = mass_cno + p * MONO_MASSES["P"]
                            if mass_cnop >= neutral_mass:
                                break

                            for s in range(max_s + 1):
                                heavy_base = mass_cnop + s * MONO_MASSES["S"]
                                if heavy_base >= neutral_mass:
                                    break

                                # Solve for Hydrogen count
                                h = int(
                                    np.rint(
                                        (neutral_mass - heavy_base) / MONO_MASSES["H"]
                                    )
                                )
                                if h < 0:
                                    continue

                                theo_mass = heavy_base + h * MONO_MASSES["H"]
                                ppm_err = (
                                    (theo_mass - neutral_mass) / neutral_mass * 1e6
                                )

                                if abs(ppm_err) > tol_ppm:
                                    continue

                                counts = {
                                    "C": c,
                                    "H": h,
                                    "N": n,
                                    "O": o,
                                    "P": p,
                                    "S": s,
                                }
                                if f > 0:
                                    counts["F"] = f
                                if cl > 0:
                                    counts["Cl"] = cl
                                if br > 0:
                                    counts["Br"] = br
                                if i_hal > 0:
                                    counts["I"] = i_hal

                                # Chemical feasibility gate
                                if not is_chemically_valid_formula(counts):
                                    continue

                                dbe, _ = calculate_dbe(counts)
                                formula_str = hill_formula(counts)

                                # Confidence score based on mass accuracy
                                confidence = math.exp(
                                    -0.5 * (ppm_err / (tol_ppm / 2.0)) ** 2
                                )

                                candidates.append(
                                    CandidateFormula(
                                        formula=formula_str,
                                        counts=counts,
                                        exact_mass=float(theo_mass),
                                        ppm_error=float(ppm_err),
                                        dbe=float(dbe),
                                        confidence_score=float(confidence),
                                    )
                                )

        # Sort descending by confidence score (closest to 0 ppm error first)
        candidates.sort(key=lambda x: x.confidence_score, reverse=True)
        return candidates[:max_candidates]
