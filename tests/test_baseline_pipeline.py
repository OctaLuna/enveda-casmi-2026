"""Unit tests for the end-to-end baseline orchestrator (DEV3-T4.5)."""

from pathlib import Path

from src.api.baseline_pipeline import BaselinePipeline
from src.api.submission import validate_submission_csv, write_submission_csv
from src.data.spectrum_parser import SpectrumRecord


def _make_record(
    molecule_id: str,
    spectrum_id: str,
    precursor_mz: float,
    label: str | None = None,
) -> SpectrumRecord:
    """Build a synthetic spectrum with 6 well-separated peaks (survives cleaning)."""
    base = precursor_mz - 100.0
    mzs = [base + 10.0 * i for i in range(6)]
    return SpectrumRecord(
        molecule_id=molecule_id,
        spectrum_id=spectrum_id,
        ms2_mzs=mzs,
        ms2_normalized_intensities=[0.2, 0.4, 0.6, 0.8, 0.9, 1.0],
        precursor_mz=precursor_mz,
        adduct="[M+H]+",
        collision_energy_ev=20.0,
        label=label,
    )


def _library() -> list[SpectrumRecord]:
    return [
        _make_record("lib_A", "sA", 300.0, "CCO"),
        _make_record("lib_B", "sB", 301.0, "CCC"),
        _make_record("lib_C", "sC", 302.0, "CCN"),
        _make_record("lib_D", "sD", 600.0, "c1ccccc1"),
    ]


def test_predict_covers_every_query_molecule():
    pipeline = BaselinePipeline().fit(_library())
    queries = [
        _make_record("q1", "q1a", 300.5),
        _make_record("q_far", "qfa", 900.0),  # no library hit
    ]
    preds = pipeline.predict(queries)
    assert set(preds) == {"q1", "q_far"}
    assert preds["q_far"] == []
    assert set(preds["q1"]) == {"CCO", "CCC", "CCN"}


def test_multi_spectrum_fusion_groups_by_molecule_id():
    pipeline = BaselinePipeline().fit(_library())
    queries = [
        _make_record("q1", "q1a", 300.0),
        _make_record("q1", "q1b", 300.2),
    ]
    preds = pipeline.predict(queries)
    assert list(preds) == ["q1"]
    # Closest precursor wins in both spectra, so it must rank first after fusion.
    assert preds["q1"][0] == "CCO"
    assert len(preds["q1"]) == len(set(preds["q1"]))


def test_predictions_truncated_to_25():
    library = [
        _make_record(f"lib_{i}", f"s{i}", 400.0 + i * 0.01, f"C{'C' * i}O")
        for i in range(40)
    ]
    pipeline = BaselinePipeline().fit(library)
    preds = pipeline.predict([_make_record("q", "qa", 400.0)])
    assert len(preds["q"]) == 25


def test_predict_is_deterministic():
    queries = [_make_record("q1", "q1a", 300.5), _make_record("q2", "q2a", 601.0)]
    first = BaselinePipeline().fit(_library()).predict(queries)
    second = BaselinePipeline().fit(_library()).predict(queries)
    assert first == second


def test_unlabeled_library_records_are_ignored():
    library = _library() + [_make_record("lib_E", "sE", 300.0, None)]
    preds = BaselinePipeline().fit(library).predict([_make_record("q", "qa", 300.0)])
    assert all(smi for smi in preds["q"])


def test_pipeline_output_roundtrips_through_submission_validator(tmp_path: Path):
    pipeline = BaselinePipeline().fit(_library())
    queries = [
        _make_record("q1", "q1a", 300.5),
        _make_record("q_far", "qfa", 900.0),
    ]
    preds = pipeline.predict(queries)
    out = write_submission_csv(preds, tmp_path / "submission.csv")
    assert validate_submission_csv(out, expected_molecule_ids=["q1", "q_far"]) is True
