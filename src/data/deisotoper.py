"""Explicit deisotoping algorithm for tandem mass spectrometry (MS/MS) spectra.

Collapses adjacent isotopic peaks (+1.0033 Da for 13C, +2.006 Da for 34S/18O/di-13C)
back into their parent monoisotopic fragment species prior to binning or embedding.
"""

from __future__ import annotations

import numpy as np

# Nominal isotope mass shifts in Daltons
DELTA_13C = 1.003355
DELTA_PLUS2 = 2.006710


def deisotope_spectrum(
    ms2_mzs: list[float] | np.ndarray,
    ms2_intensities: list[float] | np.ndarray,
    mass_tolerance_da: float = 0.015,
    accumulate_intensity: bool = True,
    max_isotope_ratio: float = 1.0,
) -> tuple[list[float], list[float]]:
    """Collapse isotopic peaks into their monoisotopic parent species.

    Args:
        ms2_mzs: Fragment m/z array.
        ms2_intensities: Corresponding peak intensity array.
        mass_tolerance_da: Absolute mass tolerance window in Daltons.
        accumulate_intensity: If True, adds isotopic peak intensity to monoisotopic parent.
        max_isotope_ratio: Maximum ratio of isotope intensity to parent intensity.
            Peaks exceeding this ratio are treated as independent fragment ions.

    Returns:
        Tuple of (clean_mzs, clean_intensities).
    """
    n_peaks = len(ms2_mzs)
    if n_peaks <= 1:
        return list(ms2_mzs), list(ms2_intensities)

    # Ensure numpy arrays sorted by m/z
    mzs = np.asarray(ms2_mzs, dtype=np.float64)
    intensities = np.asarray(ms2_intensities, dtype=np.float64)

    sort_idx = np.argsort(mzs)
    mzs = mzs[sort_idx]
    intensities = intensities[sort_idx]

    collapsed = np.zeros(n_peaks, dtype=bool)
    accumulated_ints = intensities.copy()

    for i in range(n_peaks):
        if collapsed[i]:
            continue

        parent_mz = mzs[i]
        parent_int = accumulated_ints[i]

        expected_plus1 = parent_mz + DELTA_13C
        expected_plus2 = parent_mz + DELTA_PLUS2

        # Search for subsequent peaks matching +1 or +2 isotope shift
        for j in range(i + 1, n_peaks):
            cand_mz = mzs[j]

            # If beyond +2 Da plus tolerance, no further isotopes possible for peak i
            if cand_mz > expected_plus2 + mass_tolerance_da:
                break

            if collapsed[j]:
                continue

            cand_int = intensities[j]
            # Check if intensity is plausible for an isotope
            if cand_int > parent_int * max_isotope_ratio:
                continue

            is_plus1 = abs(cand_mz - expected_plus1) <= mass_tolerance_da
            is_plus2 = abs(cand_mz - expected_plus2) <= mass_tolerance_da

            if is_plus1 or is_plus2:
                collapsed[j] = True
                if accumulate_intensity:
                    accumulated_ints[i] += cand_int

    kept_indices = np.where(~collapsed)[0]
    return mzs[kept_indices].tolist(), accumulated_ints[kept_indices].tolist()

