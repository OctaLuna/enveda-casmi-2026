"""Unit tests for baseline spectral matcher and candidate retrieval."""

from src.data.spectrum_parser import SpectrumRecord
from src.models.baseline_agent import BaselineSpectralMatcher


def test_baseline_matcher_fit_and_predict():
    ref1 = SpectrumRecord(
        molecule_id="mol_A",
        spectrum_id="spec_A",
        ms2_mzs=[120.0, 150.0],
        ms2_normalized_intensities=[0.5, 1.0],
        precursor_mz=200.0,
        adduct="[M+H]+",
        collision_energy_ev=20.0,
        label="CC(=O)O",
    )
    ref2 = SpectrumRecord(
        molecule_id="mol_B",
        spectrum_id="spec_B",
        ms2_mzs=[80.0, 110.0],
        ms2_normalized_intensities=[0.4, 1.0],
        precursor_mz=300.0,
        adduct="[M+H]+",
        collision_energy_ev=20.0,
        label="c1ccccc1",
    )

    matcher = BaselineSpectralMatcher()
    matcher.fit([ref1, ref2])

    query = SpectrumRecord(
        molecule_id="query_1",
        spectrum_id="spec_q1",
        ms2_mzs=[120.0, 150.0],
        ms2_normalized_intensities=[0.5, 1.0],
        precursor_mz=201.0,  # Closes to ref1 (diff 1.0)
        adduct="[M+H]+",
        collision_energy_ev=20.0,
    )

    preds = matcher.predict_top_k(query, k=5, precursor_tolerance_da=5.0)
    assert len(preds) == 1
    assert preds[0] == "CC(=O)O"
