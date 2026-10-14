"""Unit tests for submission generation and validation."""

from pathlib import Path

import pytest

from src.api.submission import (
    format_candidate_string,
    validate_submission_csv,
    write_submission_csv,
)


def test_format_candidate_string():
    candidates = ["CCO", "CCC", "CCN"]
    formatted = format_candidate_string(candidates, max_k=2)
    assert formatted == "CCO;CCC"


def test_write_and_validate_submission_csv(tmp_path: Path):
    sub_file = tmp_path / "submission.csv"
    preds = {
        "mol_1": ["CCO", "CCC"],
        "mol_2": ["c1ccccc1"],
    }
    write_submission_csv(preds, output_path=sub_file, max_candidates=25)
    assert sub_file.exists()

    # Should validate successfully
    is_valid = validate_submission_csv(
        sub_file, expected_molecule_ids=["mol_1", "mol_2"]
    )
    assert is_valid is True


def test_validate_submission_missing_molecules(tmp_path: Path):
    sub_file = tmp_path / "submission.csv"
    preds = {"mol_1": ["CCO"]}
    write_submission_csv(preds, output_path=sub_file)

    with pytest.raises(ValueError, match="missing 1 expected molecule_ids"):
        validate_submission_csv(sub_file, expected_molecule_ids=["mol_1", "mol_2"])
