"""Peak-based spectral similarity functions for baseline retrieval."""

from __future__ import annotations

import math

import numpy as np

from src.data.spectrum_parser import SpectrumRecord


def _validated_peaks(record: SpectrumRecord) -> tuple[np.ndarray, np.ndarray]:
    mzs = np.asarray(record.ms2_mzs, dtype=float)
    intensities = np.asarray(record.ms2_normalized_intensities, dtype=float)
    if mzs.ndim != 1 or intensities.ndim != 1 or mzs.size != intensities.size:
        raise ValueError(
            "m/z and intensity arrays must be one-dimensional and equal length"
        )
    if not np.all(np.isfinite(mzs)):
        raise ValueError("m/z values must be finite")
    if not np.all(np.isfinite(intensities)) or np.any(intensities < 0):
        raise ValueError("intensities must be finite and non-negative")
    return mzs, intensities


def _matched_peak_pairs(
    mzs_a: np.ndarray, mzs_b: np.ndarray, tolerance_da: float
) -> list[tuple[int, int]]:
    candidates = [
        (abs(float(mz_a - mz_b)), i, j)
        for i, mz_a in enumerate(mzs_a)
        for j, mz_b in enumerate(mzs_b)
        if abs(mz_a - mz_b) <= tolerance_da
    ]
    candidates.sort()
    used_a: set[int] = set()
    used_b: set[int] = set()
    pairs = []
    for _, i, j in candidates:
        if i not in used_a and j not in used_b:
            pairs.append((i, j))
            used_a.add(i)
            used_b.add(j)
    return pairs


def _check_tolerance(tolerance_da: float) -> None:
    if not math.isfinite(tolerance_da) or tolerance_da < 0:
        raise ValueError("tolerance_da must be finite and non-negative")


def cosine_similarity(
    spectrum_a: SpectrumRecord,
    spectrum_b: SpectrumRecord,
    tolerance_da: float = 0.02,
) -> float:
    """Return normalized cosine similarity from one-to-one matched peaks."""
    _check_tolerance(tolerance_da)
    mzs_a, intensities_a = _validated_peaks(spectrum_a)
    mzs_b, intensities_b = _validated_peaks(spectrum_b)
    norm_a = float(np.linalg.norm(intensities_a))
    norm_b = float(np.linalg.norm(intensities_b))
    if norm_a == 0.0 or norm_b == 0.0:
        return 0.0

    dot = sum(
        float(intensities_a[i] * intensities_b[j])
        for i, j in _matched_peak_pairs(mzs_a, mzs_b, tolerance_da)
    )
    return float(np.clip(dot / (norm_a * norm_b), 0.0, 1.0))


def _entropy(probabilities: np.ndarray) -> float:
    nonzero = probabilities[probabilities > 0.0]
    return float(-np.sum(nonzero * np.log(nonzero)))


def spectral_entropy_similarity(
    spectrum_a: SpectrumRecord,
    spectrum_b: SpectrumRecord,
    tolerance_da: float = 0.02,
) -> float:
    """Return normalized spectral-entropy similarity for two peak lists.

    Intensities are normalized to probability distributions. Matched peak
    intensities are merged before computing the entropy of the mixed spectrum.
    """
    _check_tolerance(tolerance_da)
    mzs_a, intensities_a = _validated_peaks(spectrum_a)
    mzs_b, intensities_b = _validated_peaks(spectrum_b)
    total_a = float(np.sum(intensities_a))
    total_b = float(np.sum(intensities_b))
    if total_a == 0.0 or total_b == 0.0:
        return 0.0

    probabilities_a = intensities_a / total_a
    probabilities_b = intensities_b / total_b
    pairs = _matched_peak_pairs(mzs_a, mzs_b, tolerance_da)
    used_a = {i for i, _ in pairs}
    used_b = {j for _, j in pairs}
    merged = [probabilities_a[i] + probabilities_b[j] for i, j in pairs]
    merged.extend(probabilities_a[i] for i in range(len(mzs_a)) if i not in used_a)
    merged.extend(probabilities_b[j] for j in range(len(mzs_b)) if j not in used_b)
    mixed = np.asarray(merged, dtype=float) / 2.0

    divergence = (
        2.0 * _entropy(mixed) - _entropy(probabilities_a) - _entropy(probabilities_b)
    )
    score = 1.0 - divergence / math.log(4.0)
    return float(np.clip(score, 0.0, 1.0))
