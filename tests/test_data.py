"""Unit tests for spectrum data structures and cleaning filters."""

import pytest

from src.data.spectrum_parser import SpectrumRecord


def test_spectrum_record_creation():
    record = SpectrumRecord(
        molecule_id="mol_001",
        spectrum_id="spec_001_1",
        ms2_mzs=[100.0, 150.0, 200.0],
        ms2_normalized_intensities=[0.1, 1.0, 0.4],
        precursor_mz=250.0,
        adduct="[M+H]+",
        collision_energy_ev=30.0,
        label="CCO",
    )
    assert record.molecule_id == "mol_001"
    assert record.peak_count == 3


def test_spectrum_record_length_mismatch_raises_value_error():
    with pytest.raises(ValueError, match="Peak array length mismatch"):
        SpectrumRecord(
            molecule_id="mol_001",
            spectrum_id="spec_bad",
            ms2_mzs=[100.0, 150.0],
            ms2_normalized_intensities=[0.5],
            precursor_mz=200.0,
            adduct="[M+H]+",
            collision_energy_ev=20.0,
        )


def test_filter_noise_peaks():
    record = SpectrumRecord(
        molecule_id="mol_002",
        spectrum_id="spec_noise",
        ms2_mzs=[50.0, 100.0, 150.0],
        ms2_normalized_intensities=[0.005, 1.0, 0.05],  # 0.005 is < 1%
        precursor_mz=200.0,
        adduct="[M+H]+",
        collision_energy_ev=25.0,
    )
    filtered = record.filter_noise_peaks(relative_intensity_threshold=0.01)
    assert filtered.peak_count == 2
    assert 50.0 not in filtered.ms2_mzs
    assert 100.0 in filtered.ms2_mzs


def test_filter_precursor_overhang():
    record = SpectrumRecord(
        molecule_id="mol_003",
        spectrum_id="spec_overhang",
        ms2_mzs=[100.0, 199.0, 203.0, 210.0],
        ms2_normalized_intensities=[0.2, 1.0, 0.5, 0.1],
        precursor_mz=200.0,  # Max allowed with 2.0 tolerance is 202.0
        adduct="[M+H]+",
        collision_energy_ev=35.0,
    )
    filtered = record.filter_precursor_overhang(mass_tolerance_da=2.0)
    assert filtered.peak_count == 2
    assert filtered.ms2_mzs == [100.0, 199.0]
