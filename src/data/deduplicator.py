"""Spectral deduplication for training sets in CASMI 2026.

Detects and consolidates nearly identical spectra (cosine similarity > 0.99)
belonging to the same analyte and adduct type to eliminate library representation bias.
"""

from __future__ import annotations

import logging
from collections import defaultdict
from collections.abc import Sequence

import numpy as np

from src.data.spectrum_parser import SpectrumRecord

logger = logging.getLogger(__name__)


def cosine_spectral_similarity(
    spec_a: SpectrumRecord,
    spec_b: SpectrumRecord,
    tolerance_da: float = 0.02,
) -> float:
    """Calculate cosine similarity between two spectra using peak alignment within tolerance.

    Args:
        spec_a: First spectrum record.
        spec_b: Second spectrum record.
        tolerance_da: Mass tolerance in Daltons for matching peaks.

    Returns:
        Cosine similarity as a float between 0.0 and 1.0.
    """
    mzs_a = np.asarray(spec_a.ms2_mzs, dtype=np.float64)
    ints_a = np.asarray(spec_a.ms2_normalized_intensities, dtype=np.float64)

    mzs_b = np.asarray(spec_b.ms2_mzs, dtype=np.float64)
    ints_b = np.asarray(spec_b.ms2_normalized_intensities, dtype=np.float64)

    if len(mzs_a) == 0 or len(mzs_b) == 0:
        return 0.0

    norm_a = np.linalg.norm(ints_a)
    norm_b = np.linalg.norm(ints_b)
    if norm_a == 0 or norm_b == 0:
        return 0.0

    # Match peaks from spec_a to spec_b greedily
    matched_b = np.zeros(len(mzs_b), dtype=bool)
    dot_product = 0.0

    for mz_val, int_val in zip(mzs_a, ints_a):
        diffs = np.abs(mzs_b - mz_val)
        valid_indices = np.where((diffs <= tolerance_da) & (~matched_b))[0]

        if len(valid_indices) > 0:
            best_idx = valid_indices[np.argmin(diffs[valid_indices])]
            matched_b[best_idx] = True
            dot_product += int_val * ints_b[best_idx]

    return float(dot_product / (norm_a * norm_b))


def deduplicate_spectra(
    records: Sequence[SpectrumRecord],
    similarity_threshold: float = 0.99,
    tolerance_da: float = 0.02,
) -> list[SpectrumRecord]:
    """Deduplicate spectra of the same molecule and adduct exhibiting near-identical profiles.

    Args:
        records: Collection of SpectrumRecord objects.
        similarity_threshold: Similarity cutoff above which spectra are considered redundant.
        tolerance_da: Peak matching tolerance in Daltons.

    Returns:
        Deduplicated list of SpectrumRecord objects.
    """
    groups: dict[tuple[str, str], list[SpectrumRecord]] = defaultdict(list)
    for rec in records:
        key = (rec.molecule_id, rec.adduct.strip())
        groups[key].append(rec)

    deduped: list[SpectrumRecord] = []
    total_pruned = 0

    for key, group in groups.items():
        if len(group) == 1:
            deduped.append(group[0])
            continue

        # Sort by quality: prefer spectra with more peaks and higher total intensity
        sorted_group = sorted(
            group,
            key=lambda r: (r.peak_count, sum(r.ms2_normalized_intensities)),
            reverse=True,
        )

        kept: list[SpectrumRecord] = []
        for candidate in sorted_group:
            is_duplicate = False
            for existing in kept:
                sim = cosine_spectral_similarity(
                    candidate, existing, tolerance_da=tolerance_da
                )
                if sim >= similarity_threshold:
                    is_duplicate = True
                    total_pruned += 1
                    logger.debug(
                        "Pruning duplicate spectrum %s (similar to %s, sim=%.4f)",
                        candidate.spectrum_id,
                        existing.spectrum_id,
                        sim,
                    )
                    break

            if not is_duplicate:
                kept.append(candidate)

        deduped.extend(kept)

    if total_pruned > 0:
        logger.info(
            "Spectral deduplication pruned %d redundant spectra out of %d",
            total_pruned,
            len(records),
        )

    return deduped
