"""Unit tests for the complete spectrum preprocessing pipeline."""

import pytest

from src.data.preprocessor import SpectrumPreprocessor
from src.data.spectrum_parser import SpectrumRecord


@pytest.fixture
def preprocessor():
    return SpectrumPreprocessor(
        min_relative_intensity=0.01,
        precursor_tolerance_da=2.0,
        deisotope=True,
        min_peaks=5,
        intensity_transform="sqrt",
        max_peaks_per_window=5,
        mass_window_da=50.0,
    )


def test_preprocessor_cleans_valid_spectrum(preprocessor):
    # Create record with 8 peaks: noise peak (<0.01), overhang peak (>precursor+2),
    # an isotopic peak, and 5 valid peaks
    raw_mzs = [
        10.0,  # Noise peak (intensity 0.005)
        50.0,
        51.0033,  # Isotope of 50.0
        60.0,
        80.0,
        100.0,
        120.0,  # Base peak (intensity 1.0)
        260.0,  # Overhang peak (precursor is 200.0)
    ]
    raw_ints = [0.005, 0.4, 0.05, 0.6, 0.5, 0.8, 1.0, 0.2]

    record = SpectrumRecord(
        molecule_id="mol_clean",
        spectrum_id="spec_1",
        ms2_mzs=raw_mzs,
        ms2_normalized_intensities=raw_ints,
        precursor_mz=200.0,
        adduct="[M+H]+",
        collision_energy_ev=30.0,
        label="CC(=O)O",
    )

    clean = preprocessor.preprocess_record(record, is_test=False)
    assert clean is not None
    assert clean.peak_count >= 5

    # Overhang peak 260.0 and noise peak 10.0 must be gone
    assert 260.0 not in clean.ms2_mzs
    assert 10.0 not in clean.ms2_mzs

    # Base peak must be exactly 1.0 after transformation and re-normalization
    max_intensity = max(clean.ms2_normalized_intensities)
    assert pytest.approx(max_intensity, abs=1e-5) == 1.0


def test_preprocessor_discards_sparse_spectrum_in_train(preprocessor):
    # Spectrum with only 3 peaks
    record = SpectrumRecord(
        molecule_id="mol_sparse",
        spectrum_id="spec_sparse",
        ms2_mzs=[50.0, 100.0, 150.0],
        ms2_normalized_intensities=[0.5, 1.0, 0.3],
        precursor_mz=200.0,
        adduct="[M+H]+",
        collision_energy_ev=20.0,
        label="CCO",
    )
    result = preprocessor.preprocess_record(record, is_test=False)
    assert result is None  # Must discard in train if < 5 peaks


def test_preprocessor_never_discards_in_test_mode(preprocessor):
    # In test mode, fallback must preserve the sparse spectrum
    record = SpectrumRecord(
        molecule_id="mol_test_sparse",
        spectrum_id="spec_test_sparse",
        ms2_mzs=[50.0, 100.0, 150.0],
        ms2_normalized_intensities=[0.5, 1.0, 0.3],
        precursor_mz=200.0,
        adduct="[M+H]+",
        collision_energy_ev=20.0,
    )
    result = preprocessor.preprocess_record(record, is_test=True)
    assert result is not None
    assert result.peak_count == 3
    assert max(result.ms2_normalized_intensities) == 1.0


def test_preprocessor_density_control_window(preprocessor):
    # Spectrum with 20 dense peaks within a 20 Da window [50.0 to 70.0]
    mzs = [50.0 + i for i in range(20)]
    # Decreasing intensities: 1.0 down to 0.05
    ints = [1.0 - 0.04 * i for i in range(20)]

    record = SpectrumRecord(
        molecule_id="mol_dense",
        spectrum_id="spec_dense",
        ms2_mzs=mzs,
        ms2_normalized_intensities=ints,
        precursor_mz=150.0,
        adduct="[M+H]+",
        collision_energy_ev=30.0,
    )
    clean = preprocessor.preprocess_record(record, is_test=False)
    assert clean is not None
    # With max_peaks_per_window = 5 in window 50.0 Da, must cap peaks in that window
    assert clean.peak_count <= 10


def test_preprocessor_calculates_neutral_mass(preprocessor):
    # Caffeine [M+H]+ mz = 195.087652 -> neutral mass 194.080376
    record = SpectrumRecord(
        molecule_id="mol_caff",
        spectrum_id="spec_caff",
        ms2_mzs=[50.0, 80.0, 100.0, 138.0, 195.0],
        ms2_normalized_intensities=[0.2, 0.4, 0.6, 0.9, 1.0],
        precursor_mz=195.087652,
        adduct="[M+H]+",
        collision_energy_ev=30.0,
    )
    neutral_mass = preprocessor.get_neutral_mass(record)
    assert neutral_mass is not None
    assert pytest.approx(neutral_mass, abs=1e-4) == 194.080376
