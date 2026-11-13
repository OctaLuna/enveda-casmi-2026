"""Unit tests for baseline spectral matcher and candidate retrieval."""

import pytest

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


def test_matcher_exposes_typed_cosine_candidates():
    ref = SpectrumRecord(
        "lib", "s1", [100.0, 150.0], [0.5, 1.0], 200.0, "[M+H]+", 20.0, "CCO"
    )
    query = SpectrumRecord("q", "q1", [100.0, 150.0], [0.5, 1.0], 201.0, "[M+H]+", 20.0)
    matcher = BaselineSpectralMatcher().fit([ref])
    predictions = matcher.predict_candidates(query)
    assert predictions[0].smiles == "CCO"
    assert predictions[0].score == pytest.approx(1.0)
    assert predictions[0].rank == 1
    assert matcher.predict_top_k(query) == ["CCO"]


def test_weighted_fusion_validates_weights_and_tie_breaks_by_smiles():
    import pytest

    with pytest.raises(ValueError):
        BaselineSpectralMatcher(
            strategy="weighted_fusion", cosine_weight=0.7, entropy_weight=0.2
        )
    records = [
        SpectrumRecord("b", "b", [100.0], [1.0], 200.0, "[M+H]+", 20.0, "CCO"),
        SpectrumRecord("a", "a", [100.0], [1.0], 200.0, "[M+H]+", 20.0, "CCN"),
    ]
    query = SpectrumRecord("q", "q", [100.0], [1.0], 200.0, "[M+H]+", 20.0)
    ranked = (
        BaselineSpectralMatcher(strategy="weighted_fusion")
        .fit(records)
        .predict_candidates(query)
    )
    assert [item.smiles for item in ranked] == ["CCN", "CCO"]


def test_equal_spectral_scores_tie_break_by_precursor_distance_then_smiles():
    records = [
        SpectrumRecord("lib", "farther", [100.0], [1.0], 201.0, "[M+H]+", 20.0, "CCO"),
        SpectrumRecord("lib", "closer", [100.0], [1.0], 200.2, "[M+H]+", 20.0, "CCC"),
    ]
    query = SpectrumRecord("q", "query", [100.0], [1.0], 200.0, "[M+H]+", 20.0)

    ranked = BaselineSpectralMatcher().fit(records).predict_candidates(query)

    assert [item.smiles for item in ranked] == ["CCC", "CCO"]


def test_cosine_strategy_does_not_compute_entropy(monkeypatch):
    ref = SpectrumRecord("lib", "s1", [100.0], [1.0], 200.0, "[M+H]+", 20.0, "CCO")
    query = SpectrumRecord("q", "q1", [100.0], [1.0], 200.0, "[M+H]+", 20.0)

    def unexpected_entropy(*args, **kwargs):
        raise AssertionError("cosine strategy should not calculate entropy")

    monkeypatch.setattr(
        "src.models.baseline_agent.cosine_entropy_similarities", unexpected_entropy
    )
    assert BaselineSpectralMatcher().fit([ref]).predict_top_k(query) == ["CCO"]
