"""Unit tests for spectral deduplication."""

import pytest

from src.data.deduplicator import cosine_spectral_similarity, deduplicate_spectra
from src.data.spectrum_parser import SpectrumRecord


def test_cosine_spectral_similarity_identical():
    rec1 = SpectrumRecord(
        molecule_id="mol_1",
        spectrum_id="spec_1",
        ms2_mzs=[100.0, 150.0, 200.0],
        ms2_normalized_intensities=[0.2, 0.5, 1.0],
        precursor_mz=250.0,
        adduct="[M+H]+",
        collision_energy_ev=30.0,
    )
    rec2 = SpectrumRecord(
        molecule_id="mol_1",
        spectrum_id="spec_2",
        ms2_mzs=[100.005, 150.002, 200.001],
        ms2_normalized_intensities=[0.2, 0.5, 1.0],
        precursor_mz=250.0,
        adduct="[M+H]+",
        collision_energy_ev=30.0,
    )

    sim = cosine_spectral_similarity(rec1, rec2, tolerance_da=0.01)
    assert pytest.approx(sim, abs=1e-3) == 1.0


def test_cosine_spectral_similarity_orthogonal():
    rec1 = SpectrumRecord(
        molecule_id="mol_1",
        spectrum_id="spec_1",
        ms2_mzs=[100.0, 150.0],
        ms2_normalized_intensities=[1.0, 0.5],
        precursor_mz=250.0,
        adduct="[M+H]+",
        collision_energy_ev=30.0,
    )
    rec2 = SpectrumRecord(
        molecule_id="mol_1",
        spectrum_id="spec_2",
        ms2_mzs=[200.0, 220.0],
        ms2_normalized_intensities=[1.0, 0.5],
        precursor_mz=250.0,
        adduct="[M+H]+",
        collision_energy_ev=30.0,
    )

    sim = cosine_spectral_similarity(rec1, rec2, tolerance_da=0.01)
    assert sim == 0.0


def test_deduplicate_spectra_removes_identical_spectra():
    # Two identical spectra for same molecule and same adduct
    rec1 = SpectrumRecord(
        molecule_id="mol_dup",
        spectrum_id="spec_dup_1",
        ms2_mzs=[100.0, 150.0, 200.0],
        ms2_normalized_intensities=[0.2, 0.5, 1.0],
        precursor_mz=250.0,
        adduct="[M+H]+",
        collision_energy_ev=30.0,
    )
    rec2 = SpectrumRecord(
        molecule_id="mol_dup",
        spectrum_id="spec_dup_2",
        ms2_mzs=[100.002, 150.001, 200.003],
        ms2_normalized_intensities=[0.2, 0.5, 1.0],
        precursor_mz=250.0,
        adduct="[M+H]+",
        collision_energy_ev=30.0,
    )
    # Distinct spectrum for same molecule but different adduct
    rec3 = SpectrumRecord(
        molecule_id="mol_dup",
        spectrum_id="spec_diff_adduct",
        ms2_mzs=[100.0, 150.0, 200.0],
        ms2_normalized_intensities=[0.2, 0.5, 1.0],
        precursor_mz=272.0,
        adduct="[M+Na]+",
        collision_energy_ev=30.0,
    )
    # Distinct spectrum for another molecule
    rec4 = SpectrumRecord(
        molecule_id="mol_other",
        spectrum_id="spec_other",
        ms2_mzs=[80.0, 120.0],
        ms2_normalized_intensities=[0.5, 1.0],
        precursor_mz=150.0,
        adduct="[M+H]+",
        collision_energy_ev=20.0,
    )

    records = [rec1, rec2, rec3, rec4]
    deduped = deduplicate_spectra(records, similarity_threshold=0.99)

    # rec1 and rec2 are duplicates; rec3 has different adduct; rec4 is different molecule
    assert len(deduped) == 3
    mol_dup_spec_ids = {r.spectrum_id for r in deduped if r.molecule_id == "mol_dup"}
    assert len(mol_dup_spec_ids) == 2
    assert "spec_diff_adduct" in mol_dup_spec_ids
    assert ("spec_dup_1" in mol_dup_spec_ids) ^ ("spec_dup_2" in mol_dup_spec_ids)

