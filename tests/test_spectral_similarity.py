import pytest

from src.data.spectrum_parser import SpectrumRecord
from src.models.retrieval.spectral_similarity import (
    cosine_similarity,
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


def test_tolerance_is_configurable():
    first = spectrum([50.0], [1.0])
    second = spectrum([50.03], [1.0])
    assert cosine_similarity(first, second, tolerance_da=0.02) == 0.0
    assert cosine_similarity(first, second, tolerance_da=0.04) == pytest.approx(1.0)
    assert spectral_entropy_similarity(
        first, second, tolerance_da=0.04
    ) == pytest.approx(1.0)


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
