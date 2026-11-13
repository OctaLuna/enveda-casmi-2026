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
    if not mzs_a.size or not mzs_b.size:
        return []

    # Keep the existing nearest-pair-first, one-to-one semantics while moving
    # the quadratic distance calculation and ordering into NumPy's native code.
    differences = np.abs(mzs_a[:, None] - mzs_b[None, :])
    left, right = np.nonzero(differences <= tolerance_da)
    if not left.size:
        return []

    distances = differences[left, right]
    order = np.lexsort((right, left, distances))
    used_a = np.zeros(mzs_a.size, dtype=bool)
    used_b = np.zeros(mzs_b.size, dtype=bool)
    pairs = []
    for index in order:
        i = int(left[index])
        j = int(right[index])
        if not used_a[i] and not used_b[j]:
            pairs.append((i, j))
            used_a[i] = True
            used_b[j] = True
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
    pairs = _matched_peak_pairs(mzs_a, mzs_b, tolerance_da)
    return _cosine_from_pairs(intensities_a, intensities_b, pairs)


def _entropy(probabilities: np.ndarray) -> float:
    nonzero = probabilities[probabilities > 0.0]
    return float(-np.sum(nonzero * np.log(nonzero)))


def _cosine_from_pairs(
    intensities_a: np.ndarray,
    intensities_b: np.ndarray,
    pairs: list[tuple[int, int]],
) -> float:
    norm_a = float(np.linalg.norm(intensities_a))
    norm_b = float(np.linalg.norm(intensities_b))
    if norm_a == 0.0 or norm_b == 0.0:
        return 0.0
    dot = sum(float(intensities_a[i] * intensities_b[j]) for i, j in pairs)
    return float(np.clip(dot / (norm_a * norm_b), 0.0, 1.0))


def _entropy_from_pairs(
    intensities_a: np.ndarray,
    intensities_b: np.ndarray,
    pairs: list[tuple[int, int]],
) -> float:
    total_a = float(np.sum(intensities_a))
    total_b = float(np.sum(intensities_b))
    if total_a == 0.0 or total_b == 0.0:
        return 0.0

    probabilities_a = intensities_a / total_a
    probabilities_b = intensities_b / total_b
    used_a = {i for i, _ in pairs}
    used_b = {j for _, j in pairs}
    merged = [probabilities_a[i] + probabilities_b[j] for i, j in pairs]
    merged.extend(
        probabilities_a[i] for i in range(len(intensities_a)) if i not in used_a
    )
    merged.extend(
        probabilities_b[j] for j in range(len(intensities_b)) if j not in used_b
    )
    mixed = np.asarray(merged, dtype=float) / 2.0
    divergence = (
        2.0 * _entropy(mixed) - _entropy(probabilities_a) - _entropy(probabilities_b)
    )
    return float(np.clip(1.0 - divergence / math.log(4.0), 0.0, 1.0))


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
    pairs = _matched_peak_pairs(mzs_a, mzs_b, tolerance_da)
    return _entropy_from_pairs(intensities_a, intensities_b, pairs)


def cosine_entropy_similarities(
    spectrum_a: SpectrumRecord,
    spectrum_b: SpectrumRecord,
    tolerance_da: float = 0.02,
) -> tuple[float, float]:
    """Compute cosine and entropy similarities from one shared peak match."""
    _check_tolerance(tolerance_da)
    mzs_a, intensities_a = _validated_peaks(spectrum_a)
    mzs_b, intensities_b = _validated_peaks(spectrum_b)
    pairs = _matched_peak_pairs(mzs_a, mzs_b, tolerance_da)
    return (
        _cosine_from_pairs(intensities_a, intensities_b, pairs),
        _entropy_from_pairs(intensities_a, intensities_b, pairs),
    )
