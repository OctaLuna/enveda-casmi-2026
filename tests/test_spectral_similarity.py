import pytest

from src.data.spectrum_parser import SpectrumRecord
from src.models.retrieval.spectral_similarity import (
    _matched_peak_pairs,
    cosine_similarity,
    cosine_entropy_similarities,
    spectral_entropy_similarity,
)


def spectrum(mzs, intensities):
    return SpectrumRecord(
        molecule_id="mol",
        spectrum_id="spec",
        ms2_mzs=mzs,
        ms2_normalized_intensities=intensities,
        precursor_mz=200.0,
        adduct="[M+H]+",
        collision_energy_ev=20.0,
    )


@pytest.mark.parametrize("similarity", [cosine_similarity, spectral_entropy_similarity])
def test_identical_spectra_score_one(similarity):
    record = spectrum([50.0, 75.0], [0.5, 1.0])
    assert similarity(record, record) == pytest.approx(1.0)


@pytest.mark.parametrize("similarity", [cosine_similarity, spectral_entropy_similarity])
def test_disjoint_spectra_score_zero(similarity):
    first = spectrum([50.0], [1.0])
    second = spectrum([80.0], [1.0])
    assert similarity(first, second) == pytest.approx(0.0)


def test_cosine_uses_partial_matches_and_one_to_one_peak_matching():
    query = spectrum([50.0, 60.0], [1.0, 1.0])
    reference = spectrum([50.01, 50.02], [1.0, 1.0])
    assert cosine_similarity(query, reference) == pytest.approx(0.5)


def test_peak_matching_keeps_nearest_pair_and_deterministic_tie_order():
    import numpy as np

    assert _matched_peak_pairs(
        np.array([0.0, 0.03]), np.array([0.02]), tolerance_da=0.03
    ) == [(1, 0)]
    assert _matched_peak_pairs(
        np.array([0.0, 0.02]), np.array([0.01]), tolerance_da=0.02
    ) == [(0, 0)]


def test_tolerance_is_configurable():
    first = spectrum([50.0], [1.0])
    second = spectrum([50.03], [1.0])
    assert cosine_similarity(first, second, tolerance_da=0.02) == 0.0
    assert cosine_similarity(first, second, tolerance_da=0.04) == pytest.approx(1.0)
    assert spectral_entropy_similarity(
        first, second, tolerance_da=0.04
    ) == pytest.approx(1.0)


def test_combined_similarity_reuses_matches_without_changing_scores():
    first = spectrum([50.0, 60.0, 70.0], [0.2, 1.0, 0.6])
    second = spectrum([50.01, 62.0, 70.02], [0.5, 0.8, 1.0])

    cosine, entropy = cosine_entropy_similarities(first, second)

    assert cosine == pytest.approx(cosine_similarity(first, second))
    assert entropy == pytest.approx(spectral_entropy_similarity(first, second))


@pytest.mark.parametrize("similarity", [cosine_similarity, spectral_entropy_similarity])
def test_empty_or_zero_intensity_spectra_score_zero(similarity):
    empty = spectrum([], [])
    zero = spectrum([50.0], [0.0])
    normal = spectrum([50.0], [1.0])
    assert similarity(empty, normal) == 0.0
    assert similarity(zero, normal) == 0.0


@pytest.mark.parametrize("similarity", [cosine_similarity, spectral_entropy_similarity])
def test_negative_or_non_finite_intensities_are_rejected(similarity):
    invalid = spectrum([50.0], [-1.0])
    normal = spectrum([50.0], [1.0])
    with pytest.raises(ValueError, match="finite and non-negative"):
        similarity(invalid, normal)


def test_inputs_are_not_mutated():
    first = spectrum([50.0, 60.0], [0.5, 1.0])
    second = spectrum([50.01], [1.0])
    original = (first.ms2_mzs.copy(), first.ms2_normalized_intensities.copy())
    cosine_similarity(first, second)
    spectral_entropy_similarity(first, second)
    assert first.ms2_mzs == original[0]
    assert first.ms2_normalized_intensities == original[1]


def test_invalid_tolerance_is_rejected():
    record = spectrum([50.0], [1.0])
    with pytest.raises(ValueError, match="tolerance_da"):
        cosine_similarity(record, record, tolerance_da=-0.1)
