"""Unit tests for the parquet -> submission.csv pipeline (DEV3-T4.4)."""

from pathlib import Path

import pyarrow as pa
import pyarrow.parquet as pq
import pytest

from src.api.submission import validate_submission_csv
from src.api.submission_pipeline import generate_submission

TRAIN_COLS = [
    "molecule_id",
    "spectrum_id",
    "ms2_mzs",
    "ms2_normalized_intensities",
    "precursor_mz",
    "adduct",
    "collision_energy_ev",
    "label",
]


def _peaks(mz: float) -> list[float]:
    return [mz - 100.0 + 10.0 * i for i in range(6)]


def _write(path: Path, rows: list[tuple[str, str, float, str | None]]) -> Path:
    has_label = rows[0][3] is not None
    arrays = [
        pa.array([r[0] for r in rows]),
        pa.array([r[1] for r in rows]),
        pa.array([_peaks(r[2]) for r in rows]),
        pa.array([[0.2, 0.4, 0.6, 0.8, 0.9, 1.0] for _ in rows]),
        pa.array([r[2] for r in rows]),
        pa.array(["[M+H]+" for _ in rows]),
        pa.array([20.0 for _ in rows]),
    ]
    names = TRAIN_COLS[:-1]
    if has_label:
        arrays.append(pa.array([r[3] for r in rows]))
        names = TRAIN_COLS
    pq.write_table(pa.Table.from_arrays(arrays, names=names), path)
    return path


@pytest.fixture
def parquets(tmp_path: Path) -> tuple[Path, Path]:
    train = _write(
        tmp_path / "train.parquet",
        [("a", "sa", 300.0, "CCO"), ("b", "sb", 600.0, "CCC")],
    )
    test = _write(
        tmp_path / "test.parquet",
        [("q1", "q1a", 300.5, None), ("q2", "q2a", 900.0, None)],
    )
    return train, test


def test_generate_submission_covers_all_test_molecules(parquets, tmp_path):
    train, test = parquets
    out = generate_submission(train, test, tmp_path / "out" / "submission.csv")
    assert out.exists()
    assert validate_submission_csv(out, expected_molecule_ids=["q1", "q2"]) is True
    lines = out.read_text(encoding="utf-8").splitlines()
    assert lines[0] == "molecule_id,smiles"
    assert "q1,CCO" in lines


def test_generate_submission_raises_if_a_molecule_is_missing(
    parquets, tmp_path, monkeypatch
):
    train, test = parquets
    monkeypatch.setattr(
        "src.api.submission_pipeline.write_submission_csv",
        lambda preds, output_path, **kw: _drop_one(preds, output_path),
    )
    with pytest.raises(ValueError, match="missing"):
        generate_submission(train, test, tmp_path / "submission.csv")


def _drop_one(preds, output_path):
    from src.api.submission import write_submission_csv as real

    return real({k: v for k, v in list(preds.items())[:1]}, output_path)
